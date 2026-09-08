# SOC with AI — Security Operations Center

[![Python 3.14](https://img.shields.io/badge/Python-3.14-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104-green.svg)](https://fastapi.tiangolo.com)
[![scikit-learn](https://img.shields.io/badge/scikit--learn-1.3-orange.svg)](https://scikit-learn.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> **ML-powered SOC platform that filters, prioritizes, and explains security alerts to reduce analyst burnout and accelerate incident response.**

---

## Quick Stats

| Metric | Value |
|--------|-------|
| **Source Files** | 134 |
| **Lines of Code** | 49,500+ |
| **API Endpoints** | 428 |
| **AI Models** | 6 |
| **Test Pass Rate** | 98.3% |
| **Noise Reduction** | 87.7% |
| **F1 Accuracy** | 89.2% |
| **Annualized ROI** | $3.9M |

---

## Architecture

```

                    SOC with AI Platform                          

                                                                  
                
   Dashboard     API        WebSocket    CLI             
   (HTML/JS)    (FastAPI)   (Realtime   (Python)         
                
                                                               
        
                      API Gateway Layer                           
    Auth  CSRF  Rate Limit  RBAC  Audit  HTTPS             
        
                                                               
        
                      Core Engine Layer                           
                  
      Alert    Network     AI      Threat             
     Triage    Monitor    Engine   Intel              
                  
                  
     Hunting   Playbook Compliance Forensics           
     Engine    Engine    Engine    Engine             
                  
        
                                                               
        
                      Data Layer                                 
    SQLite  PostgreSQL  In-Memory  File System                
        

```

---

## Features

### AI Models (6-Model Ensemble)

| Model | Type | Purpose |
|-------|------|---------|
| Isolation Forest | Anomaly Detection | Detect unusual patterns |
| Autoencoder | Deep Learning | Reconstruct normal behavior |
| NLP Phishing | TF-IDF + Keywords | Classify URLs/domains |
| Behavior Profiler | Statistical | Baseline user behavior |
| SHAP/LIME | Explainability | Explain AI decisions |
| RL Feedback | Reinforcement | Learn from analyst feedback |

### Security

- **Session Authentication** with 32-char random IDs
- **CSRF Protection** with per-session tokens
- **RBAC** with admin, analyst, viewer roles
- **Rate Limiting** per-IP request throttling
- **Audit Trail** for all admin actions
- **Secure Cookies** (HttpOnly, SameSite, Secure)

### Network Monitoring

- **Real-time Packet Capture** (demo/live modes)
- **Threat Heatmap** with animated attack lines
- **Network Topology** visualization
- **File Transfer Tracking** sender/receiver IPs
- **Automated Response** firewall rules, isolation

### Threat Intelligence

- **IOC Database** with 20+ known threats
- **Reputation Scoring** (0-100 scale)
- **MITRE ATT&CK Mapping** for all IOCs
- **Threat Actor Profiles** (APT28, Lazarus, etc.)
- **Feed Integration** (AbuseIPDB, VirusTotal, OTX)

### Threat Hunting

- **KQL-like Query Language** with operators
- **8 Built-in Hunting Queries**
- **Anomaly Detection** with recommendations
- **Custom Query Support**

### Automated Playbooks

- **10 Incident Response Playbooks**
- **SLA Tracking** with escalation
- **Step-by-step Execution** with approval gates
- **Rollback Capabilities**

### Compliance

- **4 Frameworks**: GDPR, HIPAA, SOC2, PCI-DSS
- **35 Controls** with status tracking
- **Report Generation** per framework
- **Audit Trail** for compliance evidence

---

## Quick Start

### Prerequisites

- Python 3.10+
- pip

### Installation

```bash
# Clone repository
git clone <repository-url>
cd "SOC project"

# Install dependencies
pip install -r requirements.txt

# Set admin password
export SOC_ADMIN_PASSWORD=your_secure_password

# Start server
python start.py
```

### Access

| URL | Description |
|-----|-------------|
| http://localhost:8002/ | Dashboard |
| http://localhost:8002/login | Login page |
| http://localhost:8002/docs | API documentation |
| http://localhost:8002/api/health | Health check |

### Default Credentials

- **Username:** admin
- **Password:** admin123 (change in production!)

---

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+K` | Open command palette |
| `Ctrl+T` | Toggle dark/light theme |
| `Ctrl+N` | Toggle notifications |
| `Ctrl+M` | Toggle system metrics |
| `?` | Show keyboard shortcuts |
| `/` | Focus search |
| `Esc` | Close any panel |

---

## API Endpoints (428)

### Authentication (16)
- POST /api/auth/login
- POST /api/auth/logout
- GET /api/auth/me
- POST /api/auth/users
- GET /api/auth/keys
- POST /api/auth/2fa/setup
- And 10 more...

### SOC with AI (43)
- GET /api/alerts
- POST /api/triage/batch
- GET /api/alerts/stats
- POST /api/feedback
- And 39 more...

### Network Monitoring (157)
- GET /api/capture/status
- POST /api/capture/demo
- GET /api/capture/feed
- GET /api/network/interfaces
- And 153 more...

### AI Classification (57)
- POST /api/classify/traffic
- GET /api/classify/stats
- POST /api/classify/phishing
- GET /api/models/status
- And 53 more...

### Threat Intelligence (14)
- GET /api/threat-intel/stats
- GET /api/threat-intel/iocs
- POST /api/threat-intel/lookup
- GET /api/threat-intel/actors
- And 10 more...

### Threat Hunting (11)
- GET /api/hunt/stats
- GET /api/hunt/queries
- POST /api/hunt/execute/{id}
- POST /api/hunt/seed
- And 7 more...

### Compliance (14)
- GET /api/compliance/stats
- GET /api/compliance/summary
- GET /api/compliance/controls
- GET /api/compliance/report/{framework}
- And 10 more...

### System Monitoring (12)
- GET /api/system/metrics
- GET /api/system/health
- GET /api/system/info
- GET /api/system/commands
- And 8 more...

---

## Project Structure

```
SOC project/
 src/
    api/                # API Layer
       routes.py       # Route registration
       shared.py       # Shared dependencies
       schemas.py      # Pydantic validation
       csrf.py         # CSRF protection
       auth.py         # Authentication
       audit.py        # Audit trail
       routers/        # 11 router files
    intelligence/       # Threat Intelligence
    compliance/         # Compliance Engine
    hunting/            # Threat Hunting
    automation/         # Automated Playbooks
    ml/                 # Machine Learning
    network/            # Network Monitoring
    trust/              # Trust Score
    db/                 # Database
    engine/             # Reporting
 static/                 # Frontend assets
 templates/              # HTML templates
 tests/                  # Test suites
 scripts/                # Utility scripts
 data/                   # Runtime data
 requirements.txt        # Dependencies
 start.py               # Entry point
 README.md              # This file
 REPORT.md              # Production report
```

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| SOC_ADMIN_PASSWORD | admin123 | Admin password |
| SOC_HTTPS | false | Enable HTTPS |
| SOC_DB_URL | sqlite:///data/soc.db | Database URL |
| SOC_INTERFACE | auto | Network interface |
| SOC_ADMIN_MODE | false | Admin mode |

---

## Testing

```bash
# Run full system test
python scripts/full_system_test.py

# Run production audit
python scripts/production_audit.py

# Run specific test suite
python -m pytest tests/ -v
```

### Test Results

- **Full System Test:** 98.3% (57/58)
- **Production Readiness:** 96% (24/25)
- **Security Score:** 85.7% (6/7)

---

## Documentation

- [README.md](README.md) - This file
- [REPORT.md](REPORT.md) - Production readiness report
- [API Documentation](http://localhost:8002/docs) - Interactive API docs

---

## License

MIT License - see [LICENSE](LICENSE) for details.

---

## Support

- **Documentation:** http://localhost:8002/docs
- **Health Check:** http://localhost:8002/api/health
- **Issue Tracker:** GitHub Issues

---

*Built by SOC analysts, for SOC analysts.*
