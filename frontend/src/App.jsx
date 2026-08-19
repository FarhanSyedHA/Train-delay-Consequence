import React, { useState, useEffect } from "react";
import { Train, Play, RotateCcw, AlertCircle, ArrowRight, ShieldCheck } from "lucide-react";
import { fetchTrips, fetchNetworkGraph, simulateDelay, resetNetwork } from "./api";
import NetworkGraph from "./components/NetworkGraph";
import MetricsCards from "./components/MetricsCards";

export default function App() {
  const [trips, setTrips] = useState([]);
  const [networkData, setNetworkData] = useState(null);
  const [selectedTripId, setSelectedTripId] = useState("");
  const [delayMinutes, setDelayMinutes] = useState(30);
  const [simulationResult, setSimulationResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // Load initial graph & trip list
  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        const [tripsRes, networkRes] = await Promise.all([fetchTrips(), fetchNetworkGraph()]);
        setTrips(tripsRes);
        setNetworkData(networkRes);
        if (tripsRes.length > 0) setSelectedTripId(tripsRes[0].id);
      } catch (err) {
        setError(err.message || "Could not connect to database backend");
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  const handleSimulate = async (e) => {
    e?.preventDefault();
    if (!selectedTripId) return;
    try {
      setLoading(true);
      setError("");
      const result = await simulateDelay(selectedTripId, Number(delayMinutes));
      setSimulationResult(result);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleReset = async () => {
    try {
      setLoading(true);
      await resetNetwork();
      setSimulationResult(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-black text-slate-100 flex flex-col">
      <header className="border-b border-slate-800 bg-gray-950/50 backdrop-blur px-6 py-4 flex items-center justify-between sticky top-0 z-30">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-green-700 rounded-lg text-white">
            <Train className="w-5 h-5" />
          </div>
          <div>
            <h1 className="text-lg font-bold text-slate-100">Train Delay Consequences</h1>
            <p className="text-xs text-slate-400">Know your next step if a train is delayed.</p>
          </div>
        </div>
        <div className="flex items-center gap-2 text-xs text-emerald-400 bg-emerald-500/10 px-3 py-1.5 rounded-full border border-emerald-500/20">
          <ShieldCheck className="w-4 h-4" />
          <span>CognoDB Works</span>
        </div>
      </header>

      {/* Main Container  can be moved to other component*/}
      <main className="flex-1 p-6 max-w-7xl mx-auto w-full grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        {/* Left Column: Controls & Impact Chains */}
        <div className="lg:col-span-4 space-y-6">
          {/* Simulator Controls Card */}
          <div className="bg-neutral-950 border border-slate-800 p-5 rounded-2xl shadow-sm">
            <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-400 mb-4">
              Inject Delay Incident
            </h2>

            {error && (
              <div className="mb-4 p-3 bg-red-500/10 border border-red-500/20 text-red-400 text-xs rounded-lg flex items-center gap-2">
                <AlertCircle className="w-4 h-4 flex-shrink-0" />
                <span>{error}</span>
              </div>
            )}

            <form onSubmit={handleSimulate} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1.5">Select Primary Train</label>
                <select
                  value={selectedTripId}
                  onChange={(e) => setSelectedTripId(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                >
                  {trips.map((t) => (
                    <option key={t.id} value={t.id}>
                      {t.train_no} — {t.name} ({t.origin_station || "Origin"} → {t.destination_station || "Terminus"})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <div className="flex justify-between text-xs mb-1.5">
                  <span className="text-slate-300 font-medium">Delay Duration</span>
                  <span className="text-green-400 font-bold">{delayMinutes} minutes</span>
                </div>
                <input
                  type="range"
                  min="5"
                  max="120"
                  step="5"
                  value={delayMinutes}
                  onChange={(e) => setDelayMinutes(e.target.value)}
                  className="w-full h-2 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-green-500"
                />
              </div>

              <div className="flex gap-3 pt-2">
                <button
                  type="submit"
                  disabled={loading}
                  className="flex-1 bg-green-600 hover:bg-green-500 disabled:opacity-50 text-white text-sm font-medium py-2.5 px-4 rounded-lg flex items-center justify-center gap-2 shadow-lg shadow-indigo-600/20 transition"
                >
                  <Play className="w-4 h-4" />
                  {loading ? "Simulating..." : "Simulate Delay"}
                </button>
                <button
                  type="button"
                  onClick={handleReset}
                  disabled={loading}
                  className="bg-slate-800 hover:bg-slate-700 disabled:opacity-50 text-slate-300 py-2.5 px-3 rounded-lg border border-slate-700 transition"
                  title="Reset Network"
                >
                  <RotateCcw className="w-4 h-4" />
                </button>
              </div>
            </form>
          </div>

          {/* Multi-Hop Traversal Chains */}
          {simulationResult && (
            <div className="bg-neutral-950 border border-slate-800 p-5 rounded-2xl">
              <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-400 mb-3">
                Dependency Propagation Paths
              </h2>
              <div className="space-y-3">
                {simulationResult.impact_chains.map((chain, idx) => (
                  <div key={idx} className="bg-neutral-950 p-3 rounded-lg border border-slate-800/80">
                    <p className="text-xs text-slate-400 mb-2 font-mono">Chain #{idx + 1}</p>
                    <div className="flex flex-wrap items-center gap-2 text-xs">
                      {chain.map((trainName, tIdx) => (
                        <React.Fragment key={tIdx}>
                          <span
                            className={`px-2 py-1 rounded font-medium ${
                              tIdx === 0
                                ? "bg-red-500/20 text-red-300 border border-red-500/30"
                                : "bg-orange-500/20 text-orange-300 border border-orange-500/30"
                            }`}
                          >
                            {trainName}
                          </span>
                          {tIdx < chain.length - 1 && <ArrowRight className="w-3.5 h-3.5 text-slate-600" />}
                        </React.Fragment>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Right Column: Visualization & Broken Transfers Table */}
        <div className="lg:col-span-8 space-y-6">
          <MetricsCards simulation={simulationResult} />

          {/* Graph Visualization Canvas */}
          <div className="space-y-2">
            <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-400">
              Live Topology & Dependency Graph
            </h2>
            <NetworkGraph
              networkData={networkData}
              simulationResult={simulationResult}
              selectedTripId={selectedTripId}
            />
          </div>

          {/* Broken Transfers Table */}
          {simulationResult && (
            <div className="bg-neutral-950 border border-slate-800 rounded-2xl p-5 overflow-hidden">
              <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-400 mb-4">
                Broken Feeder & Transfer Connections
              </h2>

              {simulationResult.broken_transfers.length === 0 ? (
                <p className="text-xs text-slate-400 py-4 text-center">
                  No broken passenger connections detected for this delay window.
                </p>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-slate-950 text-slate-400 border-b border-slate-800">
                      <tr>
                        <th className="p-3">Transfer Station</th>
                        <th className="p-3">Inbound (Delayed)</th>
                        <th className="p-3">Missed Outbound</th>
                        <th className="p-3">Window Deficit</th>
                        <th className="p-3 text-right">Stranded Passengers</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800">
                      {simulationResult.broken_transfers.map((item, idx) => (
                        <tr key={idx} className="hover:bg-slate-950/40">
                          <td className="p-3 font-semibold text-slate-200">{item.station_name}</td>
                          <td className="p-3 text-red-400">{item.inbound_train}</td>
                          <td className="p-3 text-slate-300">{item.outbound_train}</td>
                          <td className="p-3 text-amber-400">-{item.delay_exceeded_by_min} min window</td>
                          <td className="p-3 font-bold text-right text-rose-400">{item.stranded_passengers} pax</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}
        </div>

      </main>
      <footer className="border-t border-[#27272a] bg-[#18181b] px-6 py-4 text-center text-xs text-[#a1a1aa]">
        © Copyright Farhan 2026
      </footer>
    </div>
  );
}
