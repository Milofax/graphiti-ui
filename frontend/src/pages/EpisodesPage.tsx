import { useState, useEffect } from 'react';
import { api } from '../api/client';
import { IconHistory } from '@tabler/icons-react';

interface Episode {
  uuid: string;
  name: string;
  created_at: string;
  group_id: string;
  source?: string;
  content?: string;
}

export function EpisodesPage() {
  const [episodes, setEpisodes] = useState<Episode[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedEpisode, setSelectedEpisode] = useState<Episode | null>(null);

  useEffect(() => {
    const fetchEpisodes = async () => {
      try {
        const response = await api.get('/episodes');
        setEpisodes(response.data.episodes || []);
      } catch (err: any) {
        setError(err.response?.data?.detail || 'Failed to load episodes');
      } finally {
        setIsLoading(false);
      }
    };
    fetchEpisodes();
  }, []);

  const formatDate = (dateStr: string) => {
    try {
      return new Date(dateStr).toLocaleString();
    } catch {
      return dateStr;
    }
  };

  return (
    <div className="page-header d-print-none">
      <div className="row align-items-center mb-4">
        <div className="col">
          <h2 className="page-title">Episodes</h2>
          <div className="text-secondary mt-1">
            View ingested episodes in the knowledge graph
          </div>
        </div>
      </div>

      {error && (
        <div className="alert alert-danger" role="alert">
          {error}
        </div>
      )}

      <div className="row">
        {/* Episodes list */}
        <div className="col-lg-8">
          {isLoading ? (
            <div className="card">
              <div className="card-body text-center py-5">
                <div className="spinner-border text-primary" role="status" />
                <p className="mt-3 text-secondary">Loading episodes...</p>
              </div>
            </div>
          ) : episodes.length === 0 ? (
            <div className="card">
              <div className="card-body text-center py-5">
                <IconHistory size={48} className="text-secondary mb-3" />
                <p className="text-secondary mb-1">No episodes found.</p>
                <p className="text-secondary small">
                  Episodes are created when you ingest content through the MCP server.
                </p>
              </div>
            </div>
          ) : (
            <div className="card">
              <div className="table-responsive">
                <table className="table table-vcenter table-hover card-table">
                  <thead>
                    <tr>
                      <th>Name</th>
                      <th>Group</th>
                      <th>Created</th>
                    </tr>
                  </thead>
                  <tbody>
                    {episodes.map((episode) => (
                      <tr
                        key={episode.uuid}
                        onClick={() => setSelectedEpisode(episode)}
                        style={{ cursor: 'pointer' }}
                        className={selectedEpisode?.uuid === episode.uuid ? 'table-primary' : ''}
                      >
                        <td className="fw-medium">{episode.name || 'Unnamed'}</td>
                        <td className="text-secondary">{episode.group_id}</td>
                        <td className="text-secondary">{formatDate(episode.created_at)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>

        {/* Episode details */}
        <div className="col-lg-4">
          {selectedEpisode ? (
            <div className="card sticky-top" style={{ top: '1rem' }}>
              <div className="card-header">
                <h3 className="card-title">Episode Details</h3>
              </div>
              <div className="card-body">
                <dl className="row mb-0">
                  <dt className="col-4">Name</dt>
                  <dd className="col-8">{selectedEpisode.name || 'Unnamed'}</dd>

                  <dt className="col-4">UUID</dt>
                  <dd className="col-8">
                    <code className="small text-break">{selectedEpisode.uuid}</code>
                  </dd>

                  <dt className="col-4">Group</dt>
                  <dd className="col-8">{selectedEpisode.group_id}</dd>

                  <dt className="col-4">Created</dt>
                  <dd className="col-8">{formatDate(selectedEpisode.created_at)}</dd>

                  {selectedEpisode.source && (
                    <>
                      <dt className="col-4">Source</dt>
                      <dd className="col-8">{selectedEpisode.source}</dd>
                    </>
                  )}
                </dl>

                {selectedEpisode.content && (
                  <div className="mt-3">
                    <strong>Content</strong>
                    <pre className="bg-dark text-light rounded p-2 mt-1 small" style={{ maxHeight: '200px', overflow: 'auto' }}>
                      {selectedEpisode.content}
                    </pre>
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="card">
              <div className="card-body text-center py-4">
                <p className="text-secondary small mb-0">
                  Select an episode to view details
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
