const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api";

export async function fetchTrips() {
  const res = await fetch(`${API_BASE_URL}/trips`);
  if (!res.ok) throw new Error("Failed to fetch trips");
  return res.json();
}

export async function fetchNetworkGraph() {
  const res = await fetch(`${API_BASE_URL}/network`);
  if (!res.ok) throw new Error("Failed to load network graph topology");
  return res.json();
}

export async function simulateDelay(tripId, delayMinutes) {
  const res = await fetch(`${API_BASE_URL}/simulate-delay`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ trip_id: tripId, delay_minutes: delayMinutes }),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || "Simulation failed");
  }
  return res.json();
}

export async function resetNetwork() {
  const res = await fetch(`${API_BASE_URL}/reset-network`, { method: "POST" });
  if (!res.ok) throw new Error("Failed to reset network");
  return res.json();
}