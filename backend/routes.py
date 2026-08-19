from fastapi import APIRouter, HTTPException, status
from models import (
    DelaySimulationRequest,
    SimulationResponse,
    AffectedTrip,
    BrokenTransfer,
    NetworkGraphResponse,
    GraphNode,
    GraphEdge
)
from database import execute_read_query, execute_write_query

router = APIRouter(prefix="/api", tags=["Railway Graph Operations"])


@router.get("/health", status_code=status.HTTP_200_OK)
def health_check():
    """Checks whether CognoDB Cloud is reachable."""
    try:
        data = execute_read_query("RETURN 'healthy' AS status, timestamp() AS ts")
        return {"status": "ok", "database": data[0]["status"], "timestamp": data[0]["ts"]}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database unreachable: {str(e)}"
        )


@router.get("/trips")
def list_trips():
    """Returns a list of all trips to populate UI selectors."""
    query = """
    MATCH (t:Trip)
    OPTIONAL MATCH (t)-[:HAS_STOP {sequence: 1}]->(startStop:TripStop)-[:CALLS_AT]->(origin:Station)
    OPTIONAL MATCH (t)-[:HAS_STOP]->(endStop:TripStop)-[:CALLS_AT]->(dest:Station)
    WHERE NOT (endStop)-[:NEXT_STOP]->()
    RETURN 
        t.id AS id,
        t.name AS name,
        t.train_no AS train_no,
        t.type AS type,
        t.delay_min AS delay_min,
        t.status AS status,
        origin.name AS origin_station,
        dest.name AS destination_station
    ORDER BY t.train_no
    """
    return execute_read_query(query)


@router.get("/network", response_model=NetworkGraphResponse)
def get_full_network_graph():
    """Returns nodes and edges formatted for visualization."""
    stations = execute_read_query("MATCH (s:Station) RETURN s.id AS id, s.name AS name, s.city AS city")
    trips = execute_read_query("MATCH (t:Trip) RETURN t.id AS id, t.name AS name, t.train_no AS train_no, t.type AS type")
    
    rels_query = """
    MATCH (a:Trip)-[r:NEXT_SERVICE|CREW_HANDOVER]->(b:Trip)
    RETURN a.id AS source, b.id AS target, type(r) AS type, type(r) AS label
    """
    edges = execute_read_query(rels_query)

    nodes = [
        GraphNode(
            id=s["id"],
            label=s["name"],
            group="Station",
            title=f"Station: {s['name']} ({s['city']})"
        )
        for s in stations
    ]
    
    for t in trips:
        nodes.append(GraphNode(
            id=t["id"],
            label=f"{t['train_no']}: {t['name']}",
            group="Trip",
            title=f"Service: {t['name']} [{t['type']}]"
        ))

    graph_edges = [GraphEdge(**edge) for edge in edges]
    return NetworkGraphResponse(nodes=nodes, edges=graph_edges)


@router.post("/simulate-delay", response_model=SimulationResponse)
def simulate_delay(payload: DelaySimulationRequest):
    """
    Simulates knock-on delay propagation and broken passenger connections.
    Uses multi-hop Cypher path traversal over operational dependencies.
    """
    root_trip = execute_read_query(
        "MATCH (t:Trip {id: $trip_id}) RETURN t.id AS id, t.name AS name",
        {"trip_id": payload.trip_id}
    )
    if not root_trip:
        raise HTTPException(status_code=404, detail=f"Trip '{payload.trip_id}' not found.")

    root_name = root_trip[0]["name"]
    injected_delay = payload.delay_minutes

    # Multi-Hop Delay Propagation Traversal (1 to 4 hops)
    propagation_query = """
    MATCH path = (root:Trip {id: $trip_id})-[:NEXT_SERVICE|CREW_HANDOVER*1..4]->(downstream:Trip)
    WITH path, relationships(path) AS rels, nodes(path) AS trips
    RETURN 
        [t IN trips | t.id] AS trip_ids,
        [t IN trips | t.name] AS trip_names,
        [t IN trips | t.train_no] AS train_numbers,
        [r IN rels | {
            type: type(r),
            buffer: coalesce(r.turnaround_min, r.buffer_min, 0),
            min_req: coalesce(r.min_required_min, 0)
        }] AS hop_details,
        length(path) AS total_hops
    ORDER BY total_hops DESC
    """
    paths_data = execute_read_query(propagation_query, {"trip_id": payload.trip_id})

    affected_trips_dict = {}
    raw_impact_chains = []

    for entry in paths_data:
        current_delay = injected_delay
        valid_chain = [root_name]

        for i, hop in enumerate(entry["hop_details"]):
            target_id = entry["trip_ids"][i + 1]
            target_name = entry["trip_names"][i + 1]
            target_train_no = entry["train_numbers"][i + 1]
            
            # Delay absorption formula
            available_buffer = hop["buffer"] - hop["min_req"]
            absorbed_delay = max(0, current_delay - available_buffer)

            if absorbed_delay > 0:
                valid_chain.append(target_name)
                if target_id not in affected_trips_dict or affected_trips_dict[target_id].incurred_delay_min < absorbed_delay:
                    affected_trips_dict[target_id] = AffectedTrip(
                        trip_id=target_id,
                        trip_name=target_name,
                        train_no=target_train_no,
                        incurred_delay_min=absorbed_delay,
                        hops_from_root=i + 1,
                        cause=f"Cascaded via {hop['type']} (Buffer: {hop['buffer']}m, Exceeded by {absorbed_delay}m)"
                    )
            current_delay = absorbed_delay

        if len(valid_chain) > 1:
            raw_impact_chains.append(valid_chain)

    # Filter duplicate sub-chains to keep only full/maximal paths
    unique_chains = []
    for chain in raw_impact_chains:
        if not any(chain == other[:len(chain)] and len(chain) < len(other) for other in raw_impact_chains):
            if chain not in unique_chains:
                unique_chains.append(chain)

    final_impact_chains = unique_chains if unique_chains else [[root_name]]

    # Passenger Broken Transfer Query
    all_delayed_trip_ids = [payload.trip_id] + list(affected_trips_dict.keys())
    
    transfers_query = """
    MATCH (inTrip:Trip)-[:HAS_STOP]->(inStop:TripStop)-[conn:PASSENGER_TRANSFER]->(outStop:TripStop)<-[:HAS_STOP]-(outTrip:Trip)
    MATCH (inStop)-[:CALLS_AT]->(stn:Station)
    WHERE inTrip.id IN $delayed_trip_ids
    RETURN 
        inTrip.id AS inbound_trip_id,
        inTrip.name AS inbound_train,
        outTrip.id AS outbound_trip_id,
        outTrip.name AS outbound_train,
        stn.name AS station_name,
        conn.scheduled_window_min AS scheduled_window,
        conn.min_walk_min AS min_walk,
        conn.pax_volume AS pax_volume
    """
    transfer_records = execute_read_query(transfers_query, {"delayed_trip_ids": all_delayed_trip_ids})

    broken_transfers = []
    total_stranded_pax = 0

    for tr in transfer_records:
        inbound_delay = (
            injected_delay if tr["inbound_trip_id"] == payload.trip_id
            else affected_trips_dict[tr["inbound_trip_id"]].incurred_delay_min
        )
        
        slack_time = tr["scheduled_window"] - inbound_delay
        if slack_time < tr["min_walk"]:
            exceeded_by = tr["min_walk"] - slack_time
            broken_transfers.append(BrokenTransfer(
                inbound_trip=tr["inbound_trip_id"],
                inbound_train=tr["inbound_train"],
                outbound_trip=tr["outbound_trip_id"],
                outbound_train=tr["outbound_train"],
                station_name=tr["station_name"],
                scheduled_window_min=tr["scheduled_window"],
                delay_exceeded_by_min=exceeded_by,
                stranded_passengers=tr["pax_volume"]
            ))
            total_stranded_pax += tr["pax_volume"]

    return SimulationResponse(
        root_trip_id=payload.trip_id,
        root_trip_name=root_name,
        injected_delay_min=injected_delay,
        total_affected_trips=len(affected_trips_dict),
        total_broken_transfers=len(broken_transfers),
        total_affected_passengers=total_stranded_pax,
        impact_chains=final_impact_chains,
        affected_trips=list(affected_trips_dict.values()),
        broken_transfers=broken_transfers
    )


@router.post("/reset-network")
def reset_network():
    """Resets delay markers in the graph to default status."""
    execute_write_query("MATCH (t:Trip) SET t.delay_min = 0, t.status = 'ON_TIME'")
    return {"message": "All trip delays reset to 0."}