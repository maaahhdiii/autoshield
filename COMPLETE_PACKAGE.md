# 🎉 AutoShield - Complete Proxmox Deployment Package

**Status**: ✅ **READY FOR DEPLOYMENT**  
**Target Environment**: Proxmox Home Lab  
**Deployment Model**: Single LXC Container with Docker Services

---

## 📦 What's Included

This repository contains everything needed to deploy AutoShield in your Proxmox home lab:

### ✅ Working Services (Production-Ready)

1. **Kali MCP Server** - Security tools platform
   - Location: `kali-mcp/`
   - Port: 8001
   - Tools: Nmap, UFW, system monitoring, log analysis
   - Status: 100% Complete ✅

2. **Python AI Controller** - Intelligent threat analysis
   - Location: `python-ai/`
   - Port: 8000
   - Features: Threat scoring, automated response, IP reputation
   - Status: 100% Complete ✅

3. **PostgreSQL Database** - Data persistence
   - Port: 5432 (internal only)
   - Status: Configured ✅

### 🚧 Planned Services (Future)

4. **Java Backend** - REST API and business logic
   - Location: `java-backend/` (structure only)
   - Port: 8080
   - Status: 10% (directory structure created)

5. **Vaadin Frontend** - Web dashboard
   - Location: `java-backend/` (integrated)
   - Port: 8080
   - Status: 5% (planned)

---

## 🚀 Quick Deployment Guide

### Prerequisites
- Proxmox VE 7.x or 8.x
- 4 CPU cores available
- 8GB RAM available
- 50GB disk space
- Static IP for container (e.g., 192.168.1.150)

### One-Command Deployment

```bash
# 1. SSH into Proxmox host
ssh root@your-proxmox-ip

# 2. Run automated setup script
wget https://raw.githubusercontent.com/maaahhdiii/autoshield/main/scripts/setup-proxmox-lxc.sh
chmod +x setup-proxmox-lxc.sh
./setup-proxmox-lxc.sh

# 3. Follow the prompts
# - Container will be created with ID 150
# - Docker will be installed automatically
# - User 'autoshield' will be created
# - Firewall will be configured

# 4. Enter container and deploy
pct enter 150
su - autoshield
cd /opt/autoshield

# 5. Copy your AutoShield files
# From dev machine: scp -r d:\autoshild\* autoshield@192.168.1.150:/opt/autoshield/

# 6. Configure
cp .env.example .env
nano .env  # Update passwords, tokens, IPs

# 7. Start services
docker compose up -d postgres kali-mcp python-ai

# 8. Verify
curl http://localhost:8000/health
```

**Total Time**: 15-20 minutes

---

## 📁 Repository Structure

```
autoshild/
├── kali-mcp/                    # Kali MCP Server ✅
│   ├── server.py                # Main MCP server
│   ├── auth.py                  # Authentication
│   ├── config.py                # Configuration
│   ├── tools/                   # Security tools
│   │   ├── nmap_tools.py
│   │   ├── firewall_tools.py
│   │   ├── system_tools.py
│   │   └── log_tools.py
│   ├── Dockerfile               # Container config
│   └── requirements.txt         # Python dependencies
│
├── python-ai/                   # Python AI Controller ✅
│   ├── main.py                  # FastAPI application
│   ├── threat_analyzer.py       # Threat analysis engine
│   ├── mcp_client.py            # MCP client manager
│   ├── models.py                # Pydantic models
│   ├── config.py                # Configuration
│   ├── Dockerfile               # Container config
│   └── requirements.txt         # Python dependencies
│
├── java-backend/                # Java Backend (TODO) 🚧
│   └── src/main/java/com/autoshield/
│       ├── entity/              # JPA entities (empty)
│       ├── repository/          # Repositories (empty)
│       ├── service/             # Services (empty)
│       ├── controller/          # Controllers (empty)
│       └── config/              # Configuration (empty)
│
├── docs/                        # Documentation ✅
│   ├── PROXMOX_DEPLOYMENT.md    # ⭐ Proxmox LXC guide
│   ├── INSTALLATION.md          # Docker/manual install guide
│   ├── API.md                   # API reference
│   └── DEPLOYMENT_OPTIONS.md    # Deployment comparison
│
├── scripts/                     # Automation scripts ✅
│   └── setup-proxmox-lxc.sh     # Automated LXC setup
│
├── docker-compose.yml           # Docker orchestration ✅
├── .env.example                 # Configuration template ✅
├── .gitignore                   # Git ignore rules ✅
├── README.md                    # Main documentation ✅
├── QUICKSTART.md                # Quick start guide ✅
├── PROJECT_STATUS.md            # Project status ✅
├── AUDIT_REPORT.md              # Quality audit ✅
└── COMPLETE_PACKAGE.md          # This file ✅
```

---

## 🎯 Deployment Architecture

### Single LXC Container Model

```
┌─────────────────────────────────────────────────────────────┐
│  Proxmox Host (192.168.1.100)                               │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  LXC Container: autoshield-main (192.168.1.150)        │ │
│  │  (Privileged, Nesting Enabled)                         │ │
│  │                                                         │ │
│  │  ┌───────────────────────────────────────────────────┐ │ │
│  │  │  Docker Engine                                     │ │ │
│  │  │                                                    │ │ │
│  │  │  ┌──────────────────────────────────────────────┐ │ │ │
│  │  │  │  Docker Network: autoshield-network          │ │ │ │
│  │  │  │  Bridge: 172.20.0.0/16                       │ │ │ │
│  │  │  │                                              │ │ │ │
│  │  │  │  ┌────────────────┐  ┌──────────────────┐  │ │ │ │
│  │  │  │  │  postgres      │  │  python-ai       │  │ │ │ │
│  │  │  │  │  172.20.0.2    │  │  172.20.0.3      │  │ │ │ │
│  │  │  │  │  (internal)    │  │  Exposed: 8000   │  │ │ │ │
│  │  │  │  └────────────────┘  └──────────────────┘  │ │ │ │
│  │  │  │                                              │ │ │ │
│  │  │  │  ┌────────────────┐  ┌──────────────────┐  │ │ │ │
│  │  │  │  │  kali-mcp      │  │  java-backend    │  │ │ │ │
│  │  │  │  │  172.20.0.4    │  │  172.20.0.5      │  │ │ │ │
│  │  │  │  │  Exposed: 8001 │  │  Exposed: 8080   │  │ │ │ │
│  │  │  │  │                │  │  (TODO)          │  │ │ │ │
│  │  │  │  └────────────────┘  └──────────────────┘  │ │ │ │
│  │  │  └──────────────────────────────────────────────┘ │ │ │
│  │  └───────────────────────────────────────────────────┘ │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘

Access from LAN:
- AI Controller: http://192.168.1.150:8000
- Kali Tools:     http://192.168.1.150:8001
- Web Dashboard:  http://192.168.1.150:8080 (TODO)
```

---

## 🔧 Configuration Guide

### Step-by-Step Configuration

1. **Copy Environment Template**
   ```bash
   cp .env.example .env
   ```

2. **Generate Secure Passwords**
   ```bash
   # Database password
   openssl rand -base64 32
   
   # MCP authentication token
   openssl rand -hex 16
   ```

3. **Edit Configuration**
   ```bash
   nano .env
   ```

4. **Required Changes**

   ```bash
   # Database (REQUIRED)
   POSTGRES_PASSWORD=<paste-generated-password>
   
   # MCP Token (REQUIRED)
   MCP_AUTH_TOKEN=<paste-generated-token>
   
   # Your Network (REQUIRED)
   ALLOWED_IP_RANGES=192.168.0.0/16,10.0.0.0/8
   
   # Whitelist (REQUIRED - add your IPs)
   WHITELISTED_IPS=127.0.0.1,::1,192.168.1.1,192.168.1.100,192.168.1.150
   ```

5. **Optional: Proxmox Integration**

   ```bash
   # Create API token in Proxmox:
   # Datacenter → Permissions → API Tokens → Add
   
   PROXMOX_API_URL=https://192.168.1.100:8006
   PROXMOX_TOKEN_ID=autoshield@pam!monitoring
   PROXMOX_TOKEN_SECRET=<your-proxmox-token>
   ```

---

## 📊 Testing the Deployment

### Health Checks

```bash
# Inside LXC container
curl http://localhost:8000/health
curl http://localhost:8001/health

# From your network
curl http://192.168.1.150:8000/health
curl http://192.168.1.150:8001/health
```

**Expected Response**:
```json
{
  "status": "healthy",
  "mcp_connection": {
    "connected": true,
    "available_tools": 7
  }
}
```

### Send Test Security Event

```bash
curl -X POST http://192.168.1.150:8000/api/v1/security-event \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "suspicious_login",
    "source_ip": "192.168.1.200",
    "severity": "medium",
    "details": {
      "username": "test",
      "port": 22
    }
  }'
```

**Expected Behavior**:
- Threat score calculated (30-59 range for medium severity)
- Quick Nmap scan triggered (if score > 30)
- Results returned in JSON
- Event logged with correlation ID

### Check Logs

```bash
# View all logs
docker compose logs -f

# View specific service
docker compose logs -f python-ai
docker compose logs -f kali-mcp

# View last 50 lines
docker compose logs --tail=50
```

---

## 🛡️ Security Checklist

Before going live, complete these security tasks:

- [ ] **Change all default passwords** in `.env`
- [ ] **Generate strong MCP token** (32+ characters)
- [ ] **Set WHITELISTED_IPS** with your management IPs
- [ ] **Configure ALLOWED_IP_RANGES** for your network
- [ ] **Enable UFW firewall** in LXC container
- [ ] **Test IP blocking** (with non-critical test IP)
- [ ] **Review logs** for errors or warnings
- [ ] **Create Proxmox snapshot** for backup
- [ ] **Document your configuration** (save .env securely)
- [ ] **Test disaster recovery** (restore from snapshot)

---

## 📚 Documentation Reference

### Essential Reading

1. **QUICKSTART.md** - Get running in 30 minutes
2. **docs/PROXMOX_DEPLOYMENT.md** - Complete LXC deployment guide
3. **docs/DEPLOYMENT_OPTIONS.md** - Compare deployment methods
4. **docs/API.md** - API reference with examples

### Additional Resources

- **README.md** - Project overview and features
- **PROJECT_STATUS.md** - Current status and capabilities
- **AUDIT_REPORT.md** - Code quality audit
- **docs/INSTALLATION.md** - Docker Compose and manual install

---

## 🔄 Common Operations

### Start/Stop Services

```bash
cd /opt/autoshield

# Stop all services
docker compose down

# Start services
docker compose up -d

# Restart specific service
docker compose restart python-ai

# Check status
docker compose ps
```

### View Logs

```bash
# Follow all logs
docker compose logs -f

# Specific service
docker compose logs -f kali-mcp

# Last 100 lines
docker compose logs --tail=100
```

### Update AutoShield

```bash
# Pull latest code
cd /opt/autoshield
git pull

# Rebuild containers
docker compose build

# Restart services
docker compose down
docker compose up -d
```

### Backup

```bash
# Database backup
docker compose exec postgres pg_dump -U autoshield autoshield > backup-$(date +%Y%m%d).sql

# Configuration backup
tar -czf config-backup-$(date +%Y%m%d).tar.gz .env docker-compose.yml

# Or use Proxmox snapshot (recommended)
# On Proxmox host:
pct snapshot 150 autoshield-backup-$(date +%Y%m%d)
```

---

## 🎓 What You Can Do Now

With the current deployment, you can:

### ✅ Automated Threat Detection
- Receive security events via REST API
- Calculate threat scores (0-100 scale)
- Track IP reputation and event history
- Detect attack patterns (brute force, port scans)

### ✅ Automated Response
- Execute quick Nmap scans (30-60 seconds)
- Run comprehensive vulnerability scans (2-5 minutes)
- Block malicious IPs via UFW firewall
- Restart system services (whitelisted only)

### ✅ Monitoring & Analysis
- Parse authentication logs for failed logins
- Monitor system health (CPU, RAM, disk, network)
- Track blocked IPs and scan history
- Generate threat assessments with reasoning

### ✅ API Integration
- 15+ REST endpoints for all operations
- Health check endpoints
- Manual scan and block controls
- IP reputation lookups
- MCP status monitoring

---

## 🚧 What's Coming Next

### Java Backend (Module 2)
When implemented, will add:
- Persistent database storage for events
- Historical data and trending analysis
- Proxmox VM integration
- Scheduled metrics collection
- Advanced reporting

### Vaadin Frontend (Module 1)
When implemented, will add:
- Real-time dashboard with charts
- Alert management interface
- Manual security controls
- Service status monitoring
- User authentication

**Current Functionality**: Core security automation is 100% operational via API. Web UI will provide visualization when complete.

---

## 💡 Tips & Best Practices

### Resource Management
- Monitor with `docker stats`
- Set memory limits in docker-compose.yml if needed
- Review logs regularly: `docker compose logs --tail=100`
- Clean old logs periodically

### Network Security
- Keep whitelisted IPs updated
- Review blocked IPs: check logs for `block_ip_firewall`
- Test with `DRY_RUN_MODE=true` before going live
- Use VPN for external access (don't expose directly to internet)

### Maintenance
- Create weekly Proxmox snapshots
- Export database backups monthly
- Update Docker images quarterly
- Review threat scores and adjust threshold

### Troubleshooting
- Check container logs first: `docker compose logs`
- Verify MCP connection: `curl http://localhost:8001/health`
- Test from inside LXC before testing from network
- Review correlation IDs in logs for request tracking

---

## 📞 Support & Resources

### Getting Help

1. **Check Documentation**:
   - README.md for overview
   - QUICKSTART.md for setup
   - docs/PROXMOX_DEPLOYMENT.md for detailed guide
   - docs/API.md for API reference

2. **Review Logs**:
   ```bash
   docker compose logs -f
   ```

3. **Verify Health**:
   ```bash
   curl http://localhost:8000/health
   curl http://localhost:8001/health
   ```

4. **Check Status**:
   ```bash
   docker compose ps
   pct status 150
   ```

### Useful Commands

```bash
# LXC operations (on Proxmox host)
pct list                    # List all containers
pct status 150              # Check container status
pct enter 150               # Enter container
pct stop 150                # Stop container
pct start 150               # Start container
pct snapshot 150 backup     # Create snapshot
pct listsnapshot 150        # List snapshots

# Docker operations (inside LXC)
docker compose ps           # List services
docker compose logs -f      # Follow logs
docker stats                # Resource usage
docker compose restart      # Restart services
docker system prune         # Clean unused resources
```

---

## ✅ Deployment Checklist

Use this checklist to track your deployment:

### Pre-Deployment
- [ ] Proxmox host accessible
- [ ] Static IP planned (e.g., 192.168.1.150)
- [ ] DNS/DHCP updated (optional)
- [ ] Backup strategy planned

### LXC Container Setup
- [ ] Ubuntu 22.04 template downloaded
- [ ] LXC container created (CT 150)
- [ ] Privileged mode enabled
- [ ] Nesting feature enabled
- [ ] Docker installed and running
- [ ] autoshield user created
- [ ] UFW firewall configured

### AutoShield Deployment
- [ ] Files copied to `/opt/autoshield`
- [ ] `.env` configured with secure passwords
- [ ] Whitelisted IPs set correctly
- [ ] Allowed IP ranges configured
- [ ] Docker Compose services started
- [ ] Health checks passing
- [ ] Test event processed successfully

### Post-Deployment
- [ ] Systemd service created for auto-start
- [ ] Backup script configured
- [ ] Proxmox snapshot created
- [ ] Monitoring set up
- [ ] Documentation reviewed
- [ ] Team trained (if applicable)

---

## 🎉 You're Ready!

**Congratulations!** You have everything needed to deploy AutoShield in your Proxmox home lab.

### Next Steps

1. **Read QUICKSTART.md** - Get running in 30 minutes
2. **Run setup script** - Automated LXC creation
3. **Configure .env** - Set passwords and tokens
4. **Start services** - `docker compose up -d`
5. **Test deployment** - Send security events
6. **Monitor logs** - Watch for first 24 hours
7. **Create backups** - Snapshots and exports

### Success Criteria

✅ Health endpoints return "healthy"  
✅ Test security event triggers scan  
✅ Logs show no errors  
✅ Services auto-restart on failure  
✅ Backups configured  
✅ Documentation reviewed  

---

**Package Version**: 2.0.0  
**Last Updated**: November 30, 2025  
**Deployment Model**: Single Proxmox LXC Container  
**Status**: Production-Ready (Python modules)  

**🛡️ Welcome to AutoShield - Your Intelligent Security Guardian!**
