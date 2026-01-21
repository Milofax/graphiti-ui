# Graphiti Knowledge Graph

Admin-Oberfläche und MCP Interface für Graphiti Knowledge Graph.

## Features

- **Dashboard** - Service-Status (LLM, Embedder), MCP-Konfiguration
- **Visualization** - Interaktiver D3.js Graph mit Node-Details
- **Query** - Cypher Query Editor mit Graph-Auswahl
- **Config** - Entity Types, LLM/Embedding Einstellungen
- **API Keys** - Verwaltung von MCP API Keys

## Tech Stack

### Frontend
| Komponente | Technologie |
|------------|-------------|
| Framework | React 18 + TypeScript |
| Build Tool | Vite |
| UI Framework | [Tabler](https://tabler.io) (Bootstrap 5) |
| Icons | @tabler/icons-react |
| Graph Rendering | D3.js (Force-Directed Layout) |
| HTTP Client | Axios |

### Backend
| Komponente | Technologie |
|------------|-------------|
| Framework | FastAPI (Python 3.11) |
| ASGI Server | Uvicorn |
| Validation | Pydantic |
| Auth | JWT (python-jose) |
| DB Client | FalkorDB Python SDK |

### Infrastructure
| Komponente | Technologie |
|------------|-------------|
| Graph Database | FalkorDB (Redis-basiert) |
| MCP Server | zepai/knowledge-graph-mcp |
| Reverse Proxy | Traefik v2 |

## Verzeichnisstruktur

```
project/
├── README.md                   # Diese Datei
├── build.sh                    # Build-Script
└── graphiti-ui/                # UI-Projekt
    ├── Dockerfile              # Multi-Stage Build
    ├── pyproject.toml          # Python Dependencies
    ├── .env.example            # Environment Vorlage
    ├── docker-compose.example.yml  # Lokale Entwicklung
    ├── frontend/               # React Frontend
    └── src/                    # FastAPI Backend
```

## Quick Start (Entwicklung)

### Mit Docker (empfohlen)

```bash
cd project/graphiti-ui

# Environment vorbereiten
cp .env.example .env

# Lokalen Stack starten (FalkorDB + MCP + UI)
docker compose -f docker-compose.example.yml up -d

# Browser öffnen
open http://localhost:8080
```

### Ohne Docker (lokale Entwicklung)

```bash
cd project/graphiti-ui

# Backend Dependencies
pip install -e .

# Frontend Dependencies
cd frontend && npm install && cd ..

# Environment
cp .env.example .env

# FalkorDB separat starten
docker run -d -p 6379:6379 -p 3000:3000 falkordb/falkordb:latest

# Backend starten
uvicorn src.main:app --reload --port 8080

# Frontend starten (separates Terminal)
cd frontend && npm run dev
```

## Build für Produktion

```bash
# Vom project-Verzeichnis
./build.sh

# Oder manuell
cd graphiti-ui
docker build -t graphiti-ui:latest .
```

## Environment Variablen

| Variable | Beschreibung | Default |
|----------|-------------|---------|
| **API Endpoints** | | |
| `GRAPHITI_MCP_URL` | MCP Server URL (intern) | `http://graphiti-mcp:8000` |
| `GRAPHITI_MCP_EXTERNAL_URL` | MCP Server URL (extern) | `http://localhost:8000` |
| `GRAPHITI_MCP_CONTAINER` | Container Name für Restart | `graphiti-mcp` |
| `FALKORDB_BROWSER_URL` | FalkorDB Browser URL | `http://localhost:3000` |
| **FalkorDB Connection** | | |
| `FALKORDB_HOST` | Hostname | `falkordb` |
| `FALKORDB_PORT` | Port | `6379` |
| `FALKORDB_PASSWORD` | Redis Auth Passwort | _(leer)_ |
| `FALKORDB_DATABASE` | Graph Name | `graphiti` |
| **LLM/Embedding** | | |
| `OLLAMA_API_URL` | OpenAI-kompatible API URL | `http://localhost:11434/v1` |
| `OLLAMA_API_KEY` | API Key | `sk-ollama` |
| `LLM_MODEL` | LLM Model Name | `claude` |
| `EMBEDDING_MODEL` | Embedding Model | `nomic-embed-text` |
| `EMBEDDING_DIM` | Vektor-Dimensionen | `768` |
| **Auth** | | |
| `ADMIN_USERNAME` | Admin Benutzername | `admin` |
| `SECRET_KEY` | JWT Signing Key | _(auto-generiert)_ |
| `JWT_EXPIRE_MINUTES` | Session-Timeout | `480` (8h) |
| **Config** | | |
| `CONFIG_PATH` | Pfad zur config.yaml | `/config/config.yaml` |
| `DEBUG` | Debug-Modus | `false` |

## Links

- [Graphiti GitHub](https://github.com/getzep/graphiti)
- [FalkorDB](https://github.com/FalkorDB/FalkorDB)
- [Tabler UI](https://tabler.io/)
- [MCP Specification](https://modelcontextprotocol.io/)

## License

MIT
