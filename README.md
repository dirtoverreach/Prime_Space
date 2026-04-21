# Prime Space

Multi-vendor network management platform combining Juniper JUNOS Space and Cisco PRIME capabilities.

## Features

- **Device Inventory** — Add/discover Juniper (JunOS) and Cisco (IOS/IOS-XE) devices
- **Network Topology** — Auto-discover via LLDP/CDP, visualize in interactive graph
- **Config Management** — Pull/backup/diff/push configs, Jinja2 templates for bulk deployment
- **Monitoring** — SNMP polling of CPU, memory, interface counters with real-time WebSocket feed
- **Alerts** — Threshold-based rules with open/acknowledge/resolve workflow
- **Command Runner** — Run CLI commands across multiple devices in parallel (Nornir)

## Quick Start (Docker)

```bash
# 1. Copy env file and generate a Fernet key
cp .env.example .env

# 2. Generate your Fernet key and paste it into .env as FERNET_KEY
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# 3. Start all services
docker-compose up -d

# 4. Open the UI
open http://localhost
# API docs: http://localhost:8000/docs
```

## Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.12 + FastAPI |
| Task queue | Celery + Redis |
| Database | PostgreSQL 16 |
| SSH | Netmiko |
| NETCONF | ncclient |
| SNMP | pysnmp |
| Multi-vendor | NAPALM |
| Parallel execution | Nornir |
| Frontend | React + Vite + TypeScript |
| UI | Tailwind CSS |
| Topology graph | Cytoscape.js |
| Config diff | Monaco Editor |
| Charts | Recharts |

## Development

```bash
# Backend
cd backend
python -m venv .venv && source .venv/bin/activate   # or .venv\Scripts\activate on Windows
pip install -r requirements-dev.txt
cp .env.example .env  # fill in FERNET_KEY
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm run dev   # runs on http://localhost:3000, proxies /api to localhost:8000
```

## Protocols Required on Devices

| Protocol | Juniper | Cisco |
|---|---|---|
| SSH | ✓ | ✓ |
| NETCONF (port 830) | ✓ | IOS-XE only |
| SNMP v2c/v3 | ✓ | ✓ |
| LLDP | ✓ | ✓ (or CDP) |
