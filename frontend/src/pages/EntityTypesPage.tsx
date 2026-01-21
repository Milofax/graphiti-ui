import { useState, useEffect } from 'react';
import { api } from '../api/client';
import { IconCategory, IconInfoCircle } from '@tabler/icons-react';

interface EntityType {
  name: string;
  description: string;
}

export function EntityTypesPage() {
  const [entityTypes, setEntityTypes] = useState<EntityType[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchEntityTypes = async () => {
      try {
        const response = await api.get('/entity-types');
        setEntityTypes(response.data || []);
      } catch (err: any) {
        setError(err.response?.data?.detail || 'Failed to load entity types');
      } finally {
        setIsLoading(false);
      }
    };
    fetchEntityTypes();
  }, []);

  return (
    <div className="page-header d-print-none">
      <div className="row align-items-center mb-4">
        <div className="col">
          <h2 className="page-title">Entity Types</h2>
          <div className="text-secondary mt-1">
            Configured entity types for knowledge extraction
          </div>
        </div>
      </div>

      <div className="alert alert-info mb-4">
        <div className="d-flex">
          <IconInfoCircle size={20} className="me-2 flex-shrink-0" />
          <div>
            Entity types define what kinds of entities the LLM extracts from text.
            They are configured in <code>config.yaml</code> under <code>graphiti.entity_types</code>.
            Changes require an MCP server restart.
          </div>
        </div>
      </div>

      {error && (
        <div className="alert alert-danger" role="alert">
          {error}
        </div>
      )}

      {isLoading ? (
        <div className="card">
          <div className="card-body text-center py-5">
            <div className="spinner-border text-primary" role="status" />
            <p className="mt-3 text-secondary">Loading entity types...</p>
          </div>
        </div>
      ) : entityTypes.length === 0 ? (
        <div className="card">
          <div className="card-body text-center py-5">
            <IconCategory size={48} className="text-secondary mb-3" />
            <p className="text-secondary mb-0">No entity types configured.</p>
            <p className="text-secondary small mt-2">
              Add entity types in <code>config.yaml</code> under <code>graphiti.entity_types</code>
            </p>
          </div>
        </div>
      ) : (
        <div className="card">
          <div className="table-responsive">
            <table className="table table-vcenter card-table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Description (LLM Prompt)</th>
                </tr>
              </thead>
              <tbody>
                {entityTypes.map((type) => (
                  <tr key={type.name}>
                    <td><code>{type.name}</code></td>
                    <td className="text-secondary">{type.description || '-'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
