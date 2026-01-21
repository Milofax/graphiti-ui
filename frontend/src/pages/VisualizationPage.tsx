import { useEffect, useRef, useState } from 'react';
import * as d3 from 'd3';
import { api } from '../api/client';
import { useTheme } from '../contexts/ThemeContext';
import { IconRefresh, IconTrash } from '@tabler/icons-react';

interface Node {
  id: string;
  name: string;
  type: string;
  group_id?: string;
  summary?: string;
  labels?: string[];
  created_at?: string;
  attributes?: Record<string, any>;
}

interface Edge {
  source: string;
  target: string;
  type: string;
  fact?: string;
}

interface GraphData {
  nodes: Node[];
  edges: Edge[];
}

interface EntityType {
  name: string;
  description: string;
}

// Color palette for entity types
const colorPalette = [
  '#206bc4', '#2fb344', '#f76707', '#d63939', '#ae3ec9',
  '#0ca678', '#4263eb', '#f59f00', '#74b816', '#fa5252',
  '#7950f2', '#15aabf', '#e64980', '#fab005', '#12b886',
];

const defaultColor = '#667382';

export function VisualizationPage() {
  const svgRef = useRef<SVGSVGElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const { theme } = useTheme();
  const [graphData, setGraphData] = useState<GraphData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);
  const [limit, setLimit] = useState(500);
  const [groups, setGroups] = useState<string[]>([]);
  const [selectedGroup, setSelectedGroup] = useState<string>('');
  const [entityTypes, setEntityTypes] = useState<EntityType[]>([]);
  const [typeColors, setTypeColors] = useState<Record<string, string>>({});
  const [isDeleting, setIsDeleting] = useState(false);

  const handleDeleteGraph = async () => {
    if (!selectedGroup) return;
    if (!confirm(`Are you sure you want to delete the graph "${selectedGroup}"?\n\nThis will permanently delete all nodes and edges in this graph.`)) {
      return;
    }

    setIsDeleting(true);
    try {
      const response = await api.delete(`/graph/group/${selectedGroup}`);
      if (response.data.success) {
        // Remove from groups list and reset selection
        setGroups(groups.filter(g => g !== selectedGroup));
        setSelectedGroup('');
        // Trigger data refresh
        setLimit(prev => prev);
      } else {
        alert(`Failed to delete graph: ${response.data.error}`);
      }
    } catch (err: any) {
      alert(`Error deleting graph: ${err.message}`);
    } finally {
      setIsDeleting(false);
    }
  };

  // Load entity types on mount
  useEffect(() => {
    const fetchEntityTypes = async () => {
      try {
        const response = await api.get('/entity-types');
        const types = response.data || [];
        setEntityTypes(types);
        // Build color map from entity types
        const colors: Record<string, string> = {};
        types.forEach((et: EntityType, index: number) => {
          colors[et.name] = colorPalette[index % colorPalette.length];
        });
        setTypeColors(colors);
      } catch (err) {
        console.error('Failed to load entity types:', err);
      }
    };
    fetchEntityTypes();
  }, []);

  // Get color for a type
  const getTypeColor = (type: string) => typeColors[type] || defaultColor;

  useEffect(() => {
    const fetchData = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const params = new URLSearchParams({ limit: limit.toString() });
        if (selectedGroup) params.append('group_id', selectedGroup);

        const response = await api.get(`/graph/data?${params}`);
        setGraphData(response.data);

        const uniqueGroups = [...new Set(response.data.nodes.map((n: Node) => n.group_id).filter(Boolean))];
        setGroups(uniqueGroups as string[]);
      } catch (err: any) {
        setError(err.response?.data?.detail || 'Failed to load graph data');
      } finally {
        setIsLoading(false);
      }
    };
    fetchData();
  }, [limit, selectedGroup]);

  useEffect(() => {
    if (!graphData || !svgRef.current || !containerRef.current) return;

    const container = containerRef.current;
    const width = container.clientWidth;
    const height = container.clientHeight;

    d3.select(svgRef.current).selectAll('*').remove();

    const svg = d3.select(svgRef.current)
      .attr('width', width)
      .attr('height', height)
      .attr('viewBox', [0, 0, width, height]);

    const zoom = d3.zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.1, 4])
      .on('zoom', (event) => {
        g.attr('transform', event.transform);
      });

    svg.call(zoom);

    const g = svg.append('g');

    const isDark = theme === 'dark';
    const linkColor = isDark ? '#3a4859' : '#e6e7e9';
    const textColor = isDark ? '#f8fafc' : '#182433';
    const bgColor = isDark ? '#182433' : '#f8fafc';

    svg.style('background', bgColor);

    const simulation = d3.forceSimulation(graphData.nodes as d3.SimulationNodeDatum[])
      .force('link', d3.forceLink(graphData.edges)
        .id((d: any) => d.id)
        .distance(100))
      .force('charge', d3.forceManyBody().strength(-300))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide().radius(30));

    const link = g.append('g')
      .selectAll('line')
      .data(graphData.edges)
      .join('line')
      .attr('stroke', linkColor)
      .attr('stroke-width', 1.5)
      .attr('stroke-opacity', 0.6);

    const node = g.append('g')
      .selectAll('g')
      .data(graphData.nodes)
      .join('g')
      .call(d3.drag<SVGGElement, Node>()
        .on('start', (event, d: any) => {
          if (!event.active) simulation.alphaTarget(0.3).restart();
          d.fx = d.x;
          d.fy = d.y;
        })
        .on('drag', (event, d: any) => {
          d.fx = event.x;
          d.fy = event.y;
        })
        .on('end', (event, d: any) => {
          if (!event.active) simulation.alphaTarget(0);
          d.fx = null;
          d.fy = null;
        }) as any);

    node.append('circle')
      .attr('r', 12)
      .attr('fill', (d: Node) => getTypeColor(d.type))
      .attr('stroke', isDark ? '#182433' : '#ffffff')
      .attr('stroke-width', 2)
      .style('cursor', 'pointer')
      .on('click', (_, d: Node) => setSelectedNode(d));

    node.append('text')
      .text((d: Node) => d.name?.substring(0, 20) || d.id.substring(0, 8))
      .attr('x', 16)
      .attr('y', 4)
      .attr('fill', textColor)
      .attr('font-size', '12px')
      .attr('font-family', 'Inter, system-ui, sans-serif');

    simulation.on('tick', () => {
      link
        .attr('x1', (d: any) => d.source.x)
        .attr('y1', (d: any) => d.source.y)
        .attr('x2', (d: any) => d.target.x)
        .attr('y2', (d: any) => d.target.y);

      node.attr('transform', (d: any) => `translate(${d.x},${d.y})`);
    });

    return () => {
      simulation.stop();
    };
  }, [graphData, theme, typeColors]);

  return (
    <div className="d-flex flex-column" style={{ height: 'calc(100vh - 2rem)' }}>
      {/* Controls */}
      <div className="card mb-3">
        <div className="card-body py-2">
          <div className="row align-items-center">
            <div className="col-auto">
              <select
                value={selectedGroup}
                onChange={e => setSelectedGroup(e.target.value)}
                className="form-select form-select-sm"
              >
                <option value="">All Groups</option>
                {groups.map(g => (
                  <option key={g} value={g}>{g}</option>
                ))}
              </select>
            </div>
            {selectedGroup && (
              <div className="col-auto">
                <button
                  onClick={handleDeleteGraph}
                  disabled={isDeleting}
                  className="btn btn-sm btn-outline-danger"
                  title={`Delete graph "${selectedGroup}"`}
                >
                  <IconTrash size={16} className="me-1" />
                  {isDeleting ? 'Deleting...' : 'Delete Graph'}
                </button>
              </div>
            )}
            <div className="col-auto">
              <select
                value={limit}
                onChange={e => setLimit(Number(e.target.value))}
                className="form-select form-select-sm"
              >
                <option value={100}>100 Nodes</option>
                <option value={250}>250 Nodes</option>
                <option value={500}>500 Nodes</option>
                <option value={1000}>1000 Nodes</option>
              </select>
            </div>
            <div className="col-auto ms-auto text-secondary">
              {graphData && `${graphData.nodes.length} Nodes • ${graphData.edges.length} Edges`}
            </div>
          </div>
        </div>
      </div>

      {/* Graph container */}
      <div ref={containerRef} className="card flex-grow-1 position-relative">
        {isLoading && (
          <div className="position-absolute top-0 start-0 w-100 h-100 d-flex align-items-center justify-content-center bg-white bg-opacity-75">
            <div className="text-center">
              <div className="spinner-border text-primary" role="status" />
              <p className="mt-3 text-secondary">Loading graph data...</p>
            </div>
          </div>
        )}

        {error && (
          <div className="position-absolute top-0 start-0 w-100 h-100 d-flex align-items-center justify-content-center">
            <div className="text-center">
              <p className="text-danger h4 mb-2">Failed to load graph</p>
              <p className="text-secondary mb-3">{error}</p>
              <button
                onClick={() => setLimit(limit)}
                className="btn btn-primary"
              >
                <IconRefresh size={16} className="me-1" />
                Retry
              </button>
            </div>
          </div>
        )}

        <svg ref={svgRef} className="w-100 h-100" />

        {/* Legend */}
        <div className="card position-absolute" style={{ top: '1rem', left: '1rem', width: 'auto', maxHeight: 'calc(100% - 2rem)', overflowY: 'auto' }}>
          <div className="card-body py-2 px-3">
            <h4 className="card-title mb-2">Entity Types</h4>
            {entityTypes.length > 0 ? (
              entityTypes.map((et) => (
                <div key={et.name} className="d-flex align-items-center gap-2 mb-1">
                  <span className="badge" style={{ backgroundColor: getTypeColor(et.name), width: '12px', height: '12px', padding: 0 }}></span>
                  <small className="text-secondary">{et.name}</small>
                </div>
              ))
            ) : (
              <small className="text-muted">Loading...</small>
            )}
          </div>
        </div>

        {/* Node details */}
        {selectedNode && (
          <div className="card position-absolute" style={{ top: '1rem', right: '1rem', width: '380px', maxHeight: 'calc(100% - 2rem)', overflowY: 'auto' }}>
            <div className="card-header d-flex align-items-center">
              <h4 className="card-title mb-0">Node Details</h4>
              <button
                className="btn btn-close ms-auto"
                onClick={() => setSelectedNode(null)}
              />
            </div>
            <div className="card-body">
              {/* Name and Type */}
              <h3 className="mb-2">{selectedNode.name || 'Unknown'}</h3>
              <div className="mb-3">
                <span
                  className="badge me-1"
                  style={{ backgroundColor: getTypeColor(selectedNode.type), color: 'white' }}
                >
                  {selectedNode.type}
                </span>
                {selectedNode.labels?.filter(l => l !== 'Entity' && l !== selectedNode.type).map(label => (
                  <span key={label} className="badge bg-secondary me-1">{label}</span>
                ))}
              </div>

              {/* Summary */}
              {selectedNode.summary && (
                <div className="mb-3">
                  <label className="form-label text-muted small mb-1">Summary</label>
                  <p className="mb-0 small">{selectedNode.summary}</p>
                </div>
              )}

              {/* Metadata */}
              {(selectedNode.group_id || selectedNode.created_at) && (
                <div className="mb-3">
                  <label className="form-label text-muted small mb-1">Metadata</label>
                  <table className="table table-sm table-borderless mb-0">
                    <tbody>
                      {selectedNode.group_id && (
                        <tr>
                          <td className="text-muted ps-0" style={{ width: '100px' }}>Graph</td>
                          <td>{selectedNode.group_id}</td>
                        </tr>
                      )}
                      {selectedNode.created_at && (
                        <tr>
                          <td className="text-muted ps-0">Created</td>
                          <td className="small">{new Date(selectedNode.created_at).toLocaleString()}</td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              )}

              {/* Custom Attributes */}
              {selectedNode.attributes && Object.keys(selectedNode.attributes).length > 0 && (
                <div>
                  <label className="form-label text-muted small mb-1">Attributes</label>
                  <table className="table table-sm table-borderless mb-0">
                    <tbody>
                      {Object.entries(selectedNode.attributes).map(([key, value]) => (
                        <tr key={key}>
                          <td className="text-muted ps-0" style={{ width: '100px' }}>{key}</td>
                          <td className="small" style={{ wordBreak: 'break-word' }}>
                            {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
