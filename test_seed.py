# this file is to test sucessful population of congodb with nodes and relations and test if opencypher can traverse operational dependency chains. 
from seed import get_driver

# Multi-hop cascade query: Delay TR_22436 (Vande Bharat NDLS-LKO) and trace down to TR_12418 (Prayagraj Superfast)
CASCADE_QUERY = """
MATCH path = (source:Trip {id: $trip_id})-[:NEXT_SERVICE|CREW_HANDOVER*1..3]->(affected:Trip)
RETURN 
    source.name AS RootTrain,
    [n IN nodes(path) | n.name] AS ImpactChain,
    [r IN relationships(path) | type(r)] AS DependencyTypes,
    length(path) AS CascadeHops
"""

# Passenger transfer query: Check connecting feeder routes from Kanpur Central
TRANSFER_QUERY = """
MATCH (inTrip:Trip {id: $trip_id})-[:HAS_STOP]->(inStop:TripStop)-[conn:PASSENGER_TRANSFER]->(outStop:TripStop)<-[:HAS_STOP]-(outTrip:Trip)
MATCH (inStop)-[:CALLS_AT]->(stn:Station)
RETURN 
    inTrip.name AS InboundTrain,
    outTrip.name AS ConnectingTrain,
    stn.name AS TransferStation,
    conn.scheduled_window_min AS TransferWindow,
    conn.min_walk_min AS MinWalkTime,
    conn.pax_volume AS PassengerVolume
"""

def test_seed():
    driver = get_driver()
    try:
        with driver.session() as session:
            print("--- 1. Multi-Hop Delay Propagation Test ---")
            results = session.run(CASCADE_QUERY, trip_id="TR_22436").data()
            if not results:
                print("No operational cascade paths found. Ensure seed.py has run successfully.")
            for row in results:
                chain = " -> ".join(row["ImpactChain"])
                deps = " -> ".join(row["DependencyTypes"])
                print(f"Impact Chain : {chain}")
                print(f"Dependencies : {deps} (Hops: {row['CascadeHops']})\n")

            print("--- 2. Feeder Transfer Connection Test ---")
            transfers = session.run(TRANSFER_QUERY, trip_id="TR_22436").data()
            for t in transfers:
                print(f"Feeder: {t['InboundTrain']} ➔ {t['ConnectingTrain']}")
                print(f"Station: {t['TransferStation']} | Window: {t['TransferWindow']}m | Min Walk: {t['MinWalkTime']}m | Volume: {t['PassengerVolume']} pax\n")
    finally:
        driver.close()

if __name__ == "__main__":
    test_seed()