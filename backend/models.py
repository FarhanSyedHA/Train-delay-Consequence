from typing import List, Optional
from pydantic import BaseModel, Field

# to validate payload from frontent when simulate-day api is triggered.
class DelaySimulationRequest(BaseModel):
    trip_id: str = Field(..., example="TR_101", description="ID of the root delayed trip")
    delay_minutes: int = Field(..., ge=1, le=240, example=35, description="Injected delay in minutes")


# Represents an individual downstream train delayed by the ripple effect. Stores the calculated cascaded delay, how many hops away it is from the root failure, and the operational cause
class AffectedTrip(BaseModel):
    trip_id: str
    trip_name: str
    train_no: str
    incurred_delay_min: int
    hops_from_root: int
    cause: str


# Represents a failed passenger connection where incoming delays exceed the minimum walking transfer window.
class BrokenTransfer(BaseModel):
    inbound_trip: str
    inbound_train: str
    outbound_trip: str
    outbound_train: str
    station_name: str
    scheduled_window_min: int
    delay_exceeded_by_min: int
    stranded_passengers: int


# The top-level response schema returned by POST /api/simulate-delay
class SimulationResponse(BaseModel):
    root_trip_id: str
    root_trip_name: str
    injected_delay_min: int
    total_affected_trips: int
    total_broken_transfers: int
    total_affected_passengers: int
    impact_chains: List[List[str]]
    affected_trips: List[AffectedTrip]
    broken_transfers: List[BrokenTransfer]


# Formats database entities (Station or Trip) into node objects required by graph visualizers (like vis-network)
class GraphNode(BaseModel):
    id: str
    label: str
    group: str
    title: Optional[str] = None


# Formats operational relationships (:NEXT_SERVICE, :CREW_HANDOVER) into directional links with a source node ID, target node ID, relationship type, and display label
class GraphEdge(BaseModel):
    source: str
    target: str
    label: str
    type: str


# The response schema for GET /api/network
class NetworkGraphResponse(BaseModel):
    nodes: List[GraphNode]
    edges: List[GraphEdge]