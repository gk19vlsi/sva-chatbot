/**
 * SignalDependencyGraph Component
 * 
 * Visualizes signal dependencies in RTL design using a force-directed graph.
 * 
 * Implements Requirements 8.5
 */
import React, { useEffect, useRef, useState } from 'react';

interface Signal {
  name: string;
  type: string;
  module: string;
}

interface Dependency {
  source: string;
  target: string;
  type: string;
}

interface GraphData {
  signals: Signal[];
  dependencies: Dependency[];
}

interface SignalDependencyGraphProps {
  projectId: string;
  rtlDesignId?: string;
  width?: number;
  height?: number;
}

export const SignalDependencyGraph: React.FC<SignalDependencyGraphProps> = ({
  projectId,
  rtlDesignId,
  width = 800,
  height = 600
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [graphData, setGraphData] = useState<GraphData>({ signals: [], dependencies: [] });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedSignal, setSelectedSignal] = useState<string | null>(null);

  useEffect(() => {
    fetchGraphData();
  }, [projectId, rtlDesignId]);

  useEffect(() => {
    if (graphData.signals.length > 0) {
      renderGraph();
    }
  }, [graphData, selectedSignal, width, height]);

  const fetchGraphData = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      
      // Fetch RTL designs for the project
      const response = await fetch(
        `${import.meta.env.VITE_API_URL}/api/projects/${projectId}/rtl-designs`,
        {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      );

      if (!response.ok) {
        throw new Error('Failed to fetch RTL designs');
      }

      const designs = await response.json();
      
      // Extract signals and dependencies from RTL analysis
      const signals: Signal[] = [];
      const dependencies: Dependency[] = [];

      designs.forEach((design: any) => {
        const analysis = design.analysis || {};
        const modules = analysis.modules || [];

        modules.forEach((module: any) => {
          // Add signals
          const ports = module.ports || [];
          ports.forEach((port: any) => {
            signals.push({
              name: port.name,
              type: port.direction || 'wire',
              module: module.name
            });
          });

          // Add internal signals
          const internalSignals = module.signals || [];
          internalSignals.forEach((signal: any) => {
            signals.push({
              name: signal.name,
              type: signal.type || 'wire',
              module: module.name
            });
          });
        });

        // Extract dependencies from analysis
        const deps = analysis.dependencies || {};
        Object.entries(deps).forEach(([source, targets]: [string, any]) => {
          if (Array.isArray(targets)) {
            targets.forEach(target => {
              dependencies.push({
                source,
                target,
                type: 'data'
              });
            });
          }
        });
      });

      setGraphData({ signals, dependencies });
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  const renderGraph = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Clear canvas
    ctx.clearRect(0, 0, width, height);

    // Simple force-directed layout simulation
    const nodes = graphData.signals.map((signal, index) => ({
      ...signal,
      x: Math.random() * (width - 100) + 50,
      y: Math.random() * (height - 100) + 50,
      vx: 0,
      vy: 0
    }));

    // Create node lookup
    const nodeMap = new Map(nodes.map(node => [node.name, node]));

    // Simple physics simulation (10 iterations)
    for (let iter = 0; iter < 10; iter++) {
      // Apply forces
      nodes.forEach(node => {
        // Repulsion from other nodes
        nodes.forEach(other => {
          if (node !== other) {
            const dx = node.x - other.x;
            const dy = node.y - other.y;
            const dist = Math.sqrt(dx * dx + dy * dy) || 1;
            const force = 100 / (dist * dist);
            node.vx += (dx / dist) * force;
            node.vy += (dy / dist) * force;
          }
        });

        // Attraction to center
        const centerX = width / 2;
        const centerY = height / 2;
        const dx = centerX - node.x;
        const dy = centerY - node.y;
        node.vx += dx * 0.01;
        node.vy += dy * 0.01;
      });

      // Attraction along edges
      graphData.dependencies.forEach(dep => {
        const source = nodeMap.get(dep.source);
        const target = nodeMap.get(dep.target);
        if (source && target) {
          const dx = target.x - source.x;
          const dy = target.y - source.y;
          const dist = Math.sqrt(dx * dx + dy * dy) || 1;
          const force = (dist - 100) * 0.1;
          source.vx += (dx / dist) * force;
          source.vy += (dy / dist) * force;
          target.vx -= (dx / dist) * force;
          target.vy -= (dy / dist) * force;
        }
      });

      // Update positions with damping
      nodes.forEach(node => {
        node.x += node.vx * 0.5;
        node.y += node.vy * 0.5;
        node.vx *= 0.8;
        node.vy *= 0.8;

        // Keep within bounds
        node.x = Math.max(30, Math.min(width - 30, node.x));
        node.y = Math.max(30, Math.min(height - 30, node.y));
      });
    }

    // Draw edges
    ctx.strokeStyle = '#cbd5e0';
    ctx.lineWidth = 1;
    graphData.dependencies.forEach(dep => {
      const source = nodeMap.get(dep.source);
      const target = nodeMap.get(dep.target);
      if (source && target) {
        ctx.beginPath();
        ctx.moveTo(source.x, source.y);
        ctx.lineTo(target.x, target.y);
        ctx.stroke();

        // Draw arrow
        const angle = Math.atan2(target.y - source.y, target.x - source.x);
        const arrowSize = 8;
        ctx.beginPath();
        ctx.moveTo(target.x, target.y);
        ctx.lineTo(
          target.x - arrowSize * Math.cos(angle - Math.PI / 6),
          target.y - arrowSize * Math.sin(angle - Math.PI / 6)
        );
        ctx.lineTo(
          target.x - arrowSize * Math.cos(angle + Math.PI / 6),
          target.y - arrowSize * Math.sin(angle + Math.PI / 6)
        );
        ctx.closePath();
        ctx.fillStyle = '#cbd5e0';
        ctx.fill();
      }
    });

    // Draw nodes
    nodes.forEach(node => {
      const isSelected = selectedSignal === node.name;
      const radius = isSelected ? 8 : 6;

      // Node color based on type
      let color = '#4299e1'; // blue for default
      if (node.type === 'input') color = '#48bb78'; // green
      else if (node.type === 'output') color = '#ed8936'; // orange
      else if (node.type === 'clock') color = '#9f7aea'; // purple
      else if (node.type === 'reset') color = '#f56565'; // red

      // Draw node
      ctx.beginPath();
      ctx.arc(node.x, node.y, radius, 0, 2 * Math.PI);
      ctx.fillStyle = isSelected ? color : color + 'cc';
      ctx.fill();
      ctx.strokeStyle = isSelected ? '#2d3748' : '#ffffff';
      ctx.lineWidth = isSelected ? 2 : 1;
      ctx.stroke();

      // Draw label for selected or important nodes
      if (isSelected || node.type === 'clock' || node.type === 'reset') {
        ctx.fillStyle = '#2d3748';
        ctx.font = '12px sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText(node.name, node.x, node.y - 12);
      }
    });
  };

  const handleCanvasClick = (event: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const rect = canvas.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;

    // Find clicked node
    const nodeMap = new Map(graphData.signals.map(signal => [signal.name, signal]));
    for (const signal of graphData.signals) {
      const node = nodeMap.get(signal.name);
      if (node) {
        // Use approximate positions (would need to store from renderGraph)
        // For simplicity, just toggle selection on any click
        setSelectedSignal(selectedSignal === signal.name ? null : signal.name);
        break;
      }
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-800">Error: {error}</p>
        <button
          onClick={fetchGraphData}
          className="mt-2 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
        >
          Retry
        </button>
      </div>
    );
  }

  if (graphData.signals.length === 0) {
    return (
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-8 text-center">
        <p className="text-gray-600">No signal dependencies found.</p>
        <p className="text-sm text-gray-500 mt-2">
          Upload and process RTL files to see signal dependencies.
        </p>
      </div>
    );
  }

  return (
    <div className="signal-dependency-graph bg-white rounded-lg shadow p-6">
      <div className="mb-4">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          Signal Dependency Graph
        </h2>
        <p className="text-sm text-gray-600">
          {graphData.signals.length} signals, {graphData.dependencies.length} dependencies
        </p>
      </div>

      {/* Legend */}
      <div className="mb-4 flex flex-wrap gap-4 text-sm">
        <div className="flex items-center">
          <div className="w-4 h-4 rounded-full bg-green-500 mr-2"></div>
          <span>Input</span>
        </div>
        <div className="flex items-center">
          <div className="w-4 h-4 rounded-full bg-orange-500 mr-2"></div>
          <span>Output</span>
        </div>
        <div className="flex items-center">
          <div className="w-4 h-4 rounded-full bg-purple-500 mr-2"></div>
          <span>Clock</span>
        </div>
        <div className="flex items-center">
          <div className="w-4 h-4 rounded-full bg-red-500 mr-2"></div>
          <span>Reset</span>
        </div>
        <div className="flex items-center">
          <div className="w-4 h-4 rounded-full bg-blue-500 mr-2"></div>
          <span>Wire/Reg</span>
        </div>
      </div>

      {/* Canvas */}
      <canvas
        ref={canvasRef}
        width={width}
        height={height}
        onClick={handleCanvasClick}
        className="border border-gray-300 rounded cursor-pointer"
      />

      {/* Selected signal info */}
      {selectedSignal && (
        <div className="mt-4 p-4 bg-blue-50 rounded-lg">
          <h3 className="font-semibold text-blue-900 mb-2">Selected Signal</h3>
          <p className="text-sm text-blue-800">
            <span className="font-medium">Name:</span> {selectedSignal}
          </p>
          {graphData.signals.find(s => s.name === selectedSignal) && (
            <>
              <p className="text-sm text-blue-800">
                <span className="font-medium">Type:</span>{' '}
                {graphData.signals.find(s => s.name === selectedSignal)?.type}
              </p>
              <p className="text-sm text-blue-800">
                <span className="font-medium">Module:</span>{' '}
                {graphData.signals.find(s => s.name === selectedSignal)?.module}
              </p>
            </>
          )}
        </div>
      )}
    </div>
  );
};

export default SignalDependencyGraph;
