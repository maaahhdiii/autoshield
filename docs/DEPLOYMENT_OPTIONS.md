# AutoShield Deployment Options

Choose the best deployment method for your environment.

---

## 🏆 Recommended: Single Proxmox LXC Container

**Best for**: Proxmox home labs (most users)

### Architecture
```
Proxmox Host (192.168.1.100)
│
└── LXC Container: autoshield-main (192.168.1.150)
    ├── Docker Engine
    └── Docker Containers:
        ├── postgres (internal)
        ├── python-ai (exposed: 8000)
        ├── kali-mcp (exposed: 8001)
        └── java-backend (exposed: 8080) [TODO]
```

### Pros ✅
- **Easy Management**: Single container to backup/restore
- **Efficient Resources**: Share host kernel, minimal overhead
- **Network Isolation**: Docker bridge network for containers
- **Automated Setup**: One-line installation script
- **Easy Backup**: Proxmox snapshots capture entire stack
- **Port Exposure**: Only expose needed ports to LAN
- **Resource Limits**: Control CPU/RAM via Proxmox
- **Monitoring**: Integrated with Proxmox metrics

### Cons ⚠️
- **Privileged Container**: Required for Docker and security tools
- **Proxmox Only**: Requires Proxmox VE host
- **No Live Migration**: LXC containers can't migrate while running

### Requirements
- Proxmox VE 7.x or 8.x
- 4 CPU cores
- 8GB RAM
- 50GB disk space
- Static IP available

### Setup Time
- **Automated**: ~15 minutes (with script)
- **Manual**: ~30 minutes

### Setup Command
```bash
# On Proxmox host
wget https://raw.githubusercontent.com/your-org/autoshield/main/scripts/setup-proxmox-lxc.sh
chmod +x setup-proxmox-lxc.sh
./setup-proxmox-lxc.sh
```

### When to Use
- ✅ You have a Proxmox home lab
- ✅ You want easy management and backups
- ✅ You need resource efficiency
- ✅ You want all services in one place
- ✅ You're comfortable with LXC containers

---

## 🐳 Alternative 1: Docker Compose on Dedicated Server

**Best for**: Dedicated Linux servers, VPS, non-Proxmox environments

### Architecture
```
Linux Server (Ubuntu 22.04)
│
└── Docker Compose
    ├── postgres (5432)
    ├── python-ai (8000)
    ├── kali-mcp (8001)
    └── java-backend (8080) [TODO]
```

### Pros ✅
- **Platform Independent**: Works on any Linux distro
- **Native Performance**: No virtualization overhead
- **Standard Docker**: Familiar tools and workflows
- **Easy Updates**: `docker compose pull && docker compose up -d`
- **Portable**: Move to any Docker host

### Cons ⚠️
- **Host Exposure**: Services run directly on host
- **Manual Setup**: No automated script
- **Backup Complexity**: Must backup volumes separately
- **Resource Sharing**: Competes with host services

### Requirements
- Ubuntu 20.04+ / Debian 11+ / RHEL 8+
- Docker Engine 24.0+
- Docker Compose 2.20+
- 4 CPU cores
- 8GB RAM
- 50GB disk space

### Setup Time
- **With Docker**: ~20 minutes
- **Fresh Install**: ~30 minutes

### Setup Commands
```bash
# Install Docker
curl -fsSL https://get.docker.com | sh

# Clone and start
cd /opt/autoshield
cp .env.example .env
nano .env
docker compose up -d postgres kali-mcp python-ai
```

### When to Use
- ✅ You don't have Proxmox
- ✅ You have a dedicated Linux server
- ✅ You want platform independence
- ✅ You're comfortable with Docker
- ✅ You need portability

---

## 🖥️ Alternative 2: Separate Proxmox VMs

**Best for**: Maximum isolation, production environments

### Architecture
```
Proxmox Host
├── VM 1: PostgreSQL (192.168.1.151)
├── VM 2: Python AI (192.168.1.152)
├── VM 3: Kali MCP (192.168.1.153)
└── VM 4: Java Backend (192.168.1.154) [TODO]
```

### Pros ✅
- **Maximum Isolation**: Each service in own VM
- **Independent Updates**: Update one service without affecting others
- **Resource Allocation**: Dedicated CPU/RAM per service
- **Live Migration**: Can migrate VMs to other Proxmox hosts
- **Security**: Network isolation between services
- **Scalability**: Easy to add more resources

### Cons ⚠️
- **High Overhead**: 4 VMs = 4x RAM/disk overhead
- **Complex Management**: 4 systems to maintain
- **Slow Backups**: Must backup each VM separately
- **Network Complexity**: More firewall rules needed
- **Resource Intensive**: Needs powerful Proxmox host

### Requirements
- Proxmox VE 7.x or 8.x
- 8-16 CPU cores
- 16-32GB RAM
- 200GB+ disk space
- Multiple static IPs

### Setup Time
- **Per VM**: ~20 minutes
- **Total**: ~2 hours

### When to Use
- ✅ You need maximum isolation
- ✅ You have plenty of resources
- ✅ You run production workloads
- ✅ You need live migration
- ✅ You want independent scaling

---

## 🏠 Alternative 3: Manual Installation (No Docker)

**Best for**: Learning, development, custom setups

### Architecture
```
Linux Server
├── PostgreSQL (systemd service)
├── Python AI (systemd service)
├── Kali MCP (systemd service)
└── Java Backend (systemd service) [TODO]
```

### Pros ✅
- **No Containers**: Direct access to all services
- **Easy Debugging**: Standard Linux processes
- **Custom Configuration**: Full control over everything
- **Native Performance**: No containerization overhead
- **Learning**: Understand all components

### Cons ⚠️
- **Manual Setup**: Must configure everything
- **Dependency Hell**: Manage Python/Java versions manually
- **Hard to Update**: Must coordinate service updates
- **No Isolation**: Services share same environment
- **Backup Complexity**: Must backup each component

### Requirements
- Ubuntu 22.04 or Kali Linux
- Python 3.11+
- Java 21 (when backend ready)
- PostgreSQL 15+
- 4 CPU cores
- 8GB RAM
- 50GB disk space

### Setup Time
- **Experienced**: ~1 hour
- **Beginners**: ~2-3 hours

### When to Use
- ✅ You're learning the system
- ✅ You're developing AutoShield
- ✅ You need custom configurations
- ✅ You don't want Docker
- ✅ You're debugging issues

---

## 📊 Comparison Matrix

| Feature | Proxmox LXC | Docker Compose | Separate VMs | Manual Install |
|---------|-------------|----------------|--------------|----------------|
| **Ease of Setup** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ | ⭐ |
| **Resource Efficiency** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Backup/Restore** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐⭐ |
| **Isolation** | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ |
| **Update Ease** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ |
| **Portability** | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |
| **Scalability** | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ |
| **Monitoring** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ |
| **RAM Usage** | 8GB | 8GB | 16-32GB | 6GB |
| **Disk Usage** | 20GB | 20GB | 100GB+ | 15GB |
| **Setup Time** | 15 min | 20 min | 2 hours | 1-3 hours |

---

## 🎯 Decision Guide

### Choose **Proxmox LXC** if:
- ✅ You have Proxmox VE
- ✅ You want the easiest setup
- ✅ You need efficient resource usage
- ✅ You want simple backups
- ✅ You're deploying in a home lab
- ✅ **This is 90% of users** ⭐

### Choose **Docker Compose** if:
- ✅ You don't have Proxmox
- ✅ You have a dedicated Linux server
- ✅ You want platform independence
- ✅ You're familiar with Docker
- ✅ You need portability

### Choose **Separate VMs** if:
- ✅ You need maximum isolation
- ✅ You have abundant resources
- ✅ You run production workloads
- ✅ You need live migration
- ✅ You want independent scaling

### Choose **Manual Install** if:
- ✅ You're developing AutoShield
- ✅ You're learning the system
- ✅ You need custom setups
- ✅ You're debugging issues
- ✅ You don't want containers

---

## 🚀 Quick Start Commands

### Proxmox LXC (Recommended)
```bash
# On Proxmox host
wget https://raw.githubusercontent.com/your-org/autoshield/main/scripts/setup-proxmox-lxc.sh
./setup-proxmox-lxc.sh
```

### Docker Compose
```bash
# On any Linux host
curl -fsSL https://get.docker.com | sh
cd /opt/autoshield
docker compose up -d postgres kali-mcp python-ai
```

### Manual Install
```bash
# See docs/INSTALLATION.md for full guide
sudo apt install python3.11 postgresql-15
cd /opt/autoshield
pip install -r python-ai/requirements.txt
# ... (many more steps)
```

---

## 📚 Documentation by Deployment

- **Proxmox LXC**: `docs/PROXMOX_DEPLOYMENT.md` ⭐
- **Docker Compose**: `docs/INSTALLATION.md` (Docker section)
- **Manual Install**: `docs/INSTALLATION.md` (Manual section)
- **Quick Start**: `QUICKSTART.md`

---

## 💡 Migration Guide

### From Docker Compose → Proxmox LXC

1. **Backup data**:
   ```bash
   docker compose exec postgres pg_dump -U autoshield autoshield > backup.sql
   cp .env backup.env
   ```

2. **Create LXC container** (use setup script)

3. **Restore data**:
   ```bash
   # Inside LXC
   docker compose up -d postgres
   docker compose exec -T postgres psql -U autoshield autoshield < backup.sql
   docker compose up -d
   ```

### From Separate VMs → Proxmox LXC

1. **Export databases** from each VM
2. **Copy configuration files**
3. **Create LXC container**
4. **Import databases**
5. **Start services**
6. **Verify and decommission old VMs**

---

## ❓ FAQ

**Q: Can I run AutoShield on Docker Desktop (Windows/Mac)?**  
A: Not recommended. The Kali MCP server requires Linux kernel features and privileged mode. Use WSL2 on Windows or a Linux VM.

**Q: Do I need a privileged LXC container?**  
A: Yes, for Docker and security tools (Nmap, UFW) to function properly.

**Q: Can I change deployment methods later?**  
A: Yes, but requires data migration. Backup before switching.

**Q: What's the minimum RAM requirement?**  
A: 8GB for LXC/Docker, 16GB for separate VMs, 6GB for manual install.

**Q: Can I run this in the cloud?**  
A: Yes, use the Docker Compose method on a VPS. Proxmox LXC requires Proxmox host.

---

**Recommendation**: Start with **Proxmox LXC** deployment. It offers the best balance of ease, efficiency, and features for home labs. You can always migrate later if needs change.

**Next Steps**: See `QUICKSTART.md` or `docs/PROXMOX_DEPLOYMENT.md` for detailed instructions.
