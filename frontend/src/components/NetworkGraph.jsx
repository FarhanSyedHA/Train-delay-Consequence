import React, { useEffect, useRef } from "react";
import { Network } from "vis-network";
import { DataSet } from "vis-data";

export default function NetworkGraph({ networkData, simulationResult, selectedTripId }) {
  const containerRef = useRef(null);
  const networkInstanceRef = useRef(null);

  useEffect(() => {
    if (!containerRef.current || !networkData) return;

    const affectedTripIds = new Set(
      simulationResult?.affected_trips?.map((t) => t.trip_id) || []
    );

    // Map Nodes with dynamic coloring
    const formattedNodes = networkData.nodes.map((node) => {
      const isRoot = node.id === selectedTripId;
      const isAffected = affectedTripIds.has(node.id);
      const isStation = node.group === "Station";

      let bgColor = isStation ? "#1e293b" : "#0284c7"; // Slate vs Sky Blue
      let borderColor = isStation ? "#64748b" : "#38bdf8";

      if (isRoot) {
        bgColor = "#dc2626"; // Crimson for root delayed train
        borderColor = "#f87171";
      } else if (isAffected) {
        bgColor = "#ea580c"; // Orange for secondary cascaded delay
        borderColor = "#fb923c";
      }

      return {
        id: node.id,
        label: node.label,
        shape: isStation ? "diamond" : "dot",
        size: isRoot ? 24 : isStation ? 18 : 14,
        color: {
          background: bgColor,
          border: borderColor,
          highlight: { background: "#f59e0b", border: "#fbbf24" },
        },
        font: { color: "#e2e8f0", size: 12, face: "Inter, sans-serif" },
        title: node.title,
      };
    });

    const formattedEdges = networkData.edges.map((edge, idx) => ({
      id: `e-${idx}`,
      from: edge.source,
      to: edge.target,
      label: edge.label,
      arrows: "to",
      color: { color: "#475569", highlight: "#f59e0b" },
      font: { color: "#94a3b8", size: 10, align: "middle" },
      smooth: { type: "cubicBezier", roundness: 0.2 },
    }));

    const data = {
      nodes: new DataSet(formattedNodes),
      edges: new DataSet(formattedEdges),
    };

    const options = {
      physics: {
        stabilization: true,
        barnesHut: { gravitationalConstant: -3000, springLength: 120 },
      },
      interaction: { hover: true, tooltipDelay: 100 },
      nodes: { borderWidth: 2 },
    };

    if (networkInstanceRef.current) {
      networkInstanceRef.current.destroy();
    }

    networkInstanceRef.current = new Network(containerRef.current, data, options);

    return () => {
      if (networkInstanceRef.current) networkInstanceRef.current.destroy();
    };
  }, [networkData, simulationResult, selectedTripId]);

  return (
    <div className="relative w-full h-[520px] bg-slate-900/60 rounded-xl border border-slate-800 overflow-hidden shadow-inner">
      <div className="absolute top-3 left-3 z-10 flex items-center gap-4 bg-slate-950/80 px-3 py-1.5 rounded-lg border border-slate-800 text-xs text-slate-300">
        <span className="flex items-center gap-1.5">
          <span className="w-3 h-3 rounded-full bg-red-600 inline-block"></span> Root Delayed Train
        </span>
        <span className="flex items-center gap-1.5">
          <span className="w-3 h-3 rounded-full bg-orange-500 inline-block"></span> Knock-on Delay
        </span>
        <span className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rotate-45 bg-slate-800 border border-slate-600 inline-block"></span> Station Hub
        </span>
      </div>
      <div ref={containerRef} className="w-full h-full" />
    </div>
  );
}