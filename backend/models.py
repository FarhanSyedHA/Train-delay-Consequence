from typing import List, Optional
from pydantic import BaseModel, Field


class DelaySimulationRequest(BaseModel):
    trip_id: str = Field(..., example="TR_101", description="ID of the root delayed trip")
    delay_minutes: int = Field(..., ge=1, le=240, example=35, description="Injected delay in minutes")


class AffectedTrip(BaseModel):
    trip_id: str
    trip_name: str
    train_no: str
    incurred_delay_min: int
    hops_from_root: int
    cause: str


class BrokenTransfer(BaseModel):
    inbound_trip: str
    inbound_train: str
    outbound_trip: str
    outbound_train: str
    station_name: str
    scheduled_window_min: int
    delay_exceeded_by_min: int
    stranded_passengers: int


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


class GraphNode(BaseModel):
    id: str
    label: str
    group: str
    title: Optional[str] = None


class GraphEdge(BaseModel):
    source: str
    target: str
    label: str
    type: str


class NetworkGraphResponse(BaseModel):
    nodes: List[GraphNode]
    edges: List[GraphEdge]