# AutoShield Proxmox LXC Container Deployment Guide

Complete guide for deploying AutoShield in a single Proxmox LXC container running Docker.

## 📋 Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Prerequisites](#prerequisites)
3. [LXC Container Setup](#lxc-container-setup)
4. [AutoShield Installation](#autoshield-installation)
5. [Network Configuration](#network-configuration)
6. [Firewall Rules](#firewall-rules)
7. [Monitoring & Maintenance](#monitoring--maintenance)
8. [Troubleshooting](#troubleshooting)
9. [Backup & Recovery](#backup--recovery)

---

## 🏗️ Architecture Overview

```
Proxmox Host (192.168.1.100)
│
└── LXC Container: autoshield-main (192.168.1.150)
    ├── Docker Engine
    └── Docker Containers:
        ├── autoshield-postgres (internal: 172.20.0.2)
        ├── autoshield-ai (internal: 172.20.0.3, exposed: 8000)
        ├── autoshield-kali (internal: 172.20.0.4, exposed: 8001)
        └── autoshield-backend (internal: 172.20.0.5, exposed: 8080) [TODO]
```

**Key Benefits**:
- ✅ Single LXC container = easy management
- ✅ All services isolated in Docker containers
- ✅ Persistent storage in LXC filesystem
- ✅ Easy backup (snapshot entire LXC)
- ✅ Network isolation with Docker bridge
- ✅ Resource limits via Proxmox controls

---

## 🔧 Prerequisites

### Proxmox Host Requirements
- **Proxmox VE**: 7.x or 8.x
- **CPU**: 4+ cores available
- **RAM**: 8GB+ available
- **Storage**: 50GB+ free space
- **Network**: Bridge interface (vmbr0)

### Network Planning
- **LXC Container IP**: Static IP in your LAN (e.g., 192.168.1.150)
- **Exposed Ports**: 8000 (AI API), 8001 (Kali Tools), 8080 (Web UI - TODO)
- **Internal Network**: 172.20.0.0/16 (Docker bridge)

---

## 🚀 LXC Container Setup

### Step 1: Download Ubuntu LXC Template

```bash
# SSH into Proxmox host
ssh root@proxmox-host

# Download Ubuntu 22.04 LXC template
pveam update
pveam available | grep ubuntu-22.04
pveam download local ubuntu-22.04-standard_22.04-1_amd64.tar.zst
```

### Step 2: Create Privileged LXC Container

AutoShield requires a **privileged container** for Docker networking and security tools.

**Via Proxmox Web UI**:

1. Navigate to **Datacenter → Your Node → Create CT**
2. Configure as follows:

**General Tab**:
- **CT ID**: 150 (or your preference)
- **Hostname**: `autoshield-main`
- **Password**: Set strong root password
- ✅ **Unprivileged container**: UNCHECKED (must be privileged for Docker)
- **SSH public key**: Optional (recommended)

**Template Tab**:
- **Storage**: local
- **Template**: ubuntu-22.04-standard_22.04-1_amd64.tar.zst

**Root Disk Tab**:
- **Storage**: local-lvm (or your preferred storage)
- **Disk size**: 50 GB
- **ACL**: Enabled

**CPU Tab**:
- **Cores**: 4
- **CPU limit**: 4 (100%)
- **CPU units**: 1024

**Memory Tab**:
- **Memory**: 8192 MB (8GB)
- **Swap**: 2048 MB (2GB)

**Network Tab**:
- **Name**: eth0
- **Bridge**: vmbr0
- **IPv4**: Static (e.g., 192.168.1.150/24)
- **Gateway**: Your router (e.g., 192.168.1.1)
- **IPv6**: DHCP (or disabled)
- **Firewall**: Enabled

**DNS Tab**:
- **DNS domain**: Your domain (optional)
- **DNS servers**: 8.8.8.8, 8.8.4.4 (or your DNS)

3. Click **Finish** (do not start yet)

### Step 3: Enable Required Features

```bash
# SSH into Proxmox host
ssh root@proxmox-host

# Edit LXC config to enable Docker features
nano /etc/pve/lxc/150.conf
```

**Add these lines**:
```bash
# Docker features
lxc.apparmor.profile: unconfined
lxc.cgroup2.devices.allow: a
lxc.cap.drop:
lxc.mount.auto: proc:rw sys:rw cgroup:rw

# Nesting for Docker
lxc.cgroup2.devices.allow: c 10:200 rwm
features: keyctl=1,nesting=1

# Network capabilities
lxc.cgroup2.devices.allow: b 7:* rwm
lxc.cgroup2.devices.allow: c 10:237 rwm
```

**Save and exit** (Ctrl+X, Y, Enter)

### Step 4: Start LXC Container

```bash
# Start the container
pct start 150

# Verify it's running
pct status 150

# Enter the container
pct enter 150
```

---

## 📦 AutoShield Installation

### Step 1: Update Ubuntu & Install Prerequisites

```bash
# Inside LXC container
apt update && apt upgrade -y

# Install required packages
apt install -y \
    curl \
    wget \
    git \
    nano \
    htop \
    net-tools \
    ca-certificates \
    gnupg \
    lsb-release \
    sudo \
    ufw

# Create autoshield user
useradd -m -s /bin/bash autoshield
usermod -aG sudo autoshield
echo "autoshield ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers.d/autoshield
```

### Step 2: Install Docker Engine

```bash
# Add Docker's official GPG key
mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# Set up Docker repository
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker Engine
apt update
apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Add autoshield user to docker group
usermod -aG docker autoshield

# Verify Docker installation
docker --version
docker compose version

# Test Docker
docker run hello-world
```

### Step 3: Configure Docker for AutoShield

```bash
# Create Docker daemon configuration
cat > /etc/docker/daemon.json <<EOF
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  },
  "storage-driver": "overlay2",
  "live-restore": true,
  "userland-proxy": false
}
EOF

# Restart Docker
systemctl restart docker
systemctl enable docker

# Verify Docker is running
systemctl status docker
```

### Step 4: Clone AutoShield Repository

```bash
# Switch to autoshield user
su - autoshield

# Create project directory
mkdir -p /opt/autoshield
cd /opt/autoshield

# Clone repository (or copy files)
# Option 1: If you have a git repo
git clone https://github.com/maaahhdiii/autoshield.git .

# Option 2: Copy from development machine
# On your dev machine:
# scp -r d:\autoshild/* autoshield@192.168.1.150:/opt/autoshield/

# Verify files are present
ls -la
# Should see: kali-mcp/ python-ai/ java-backend/ docs/ docker-compose.yml .env.example
```

### Step 5: Configure Environment

```bash
# Still as autoshield user
cd /opt/autoshield

# Copy environment template
cp .env.example .env

# Edit configuration
nano .env
```

**Critical settings**:
```bash
# Database password (CHANGE THIS!)
POSTGRES_PASSWORD=your_super_secure_password_here

# MCP authentication token (generate strong token)
MCP_AUTH_TOKEN=your_mcp_auth_token_min_32_chars

# JWT secret (only needed when Java backend is ready)
JWT_SECRET=your_jwt_secret_minimum_256_bits_long

# Proxmox API (your Proxmox host)
PROXMOX_API_URL=https://192.168.1.100:8006
PROXMOX_TOKEN_ID=autoshield@pam!monitoring
PROXMOX_TOKEN_SECRET=your-proxmox-token-secret

# IP ranges to scan (your LAN)
ALLOWED_IP_RANGES=192.168.0.0/16,10.0.0.0/8

# Threat detection
THREAT_SCORE_THRESHOLD=70
ENABLE_AUTO_BLOCK=true
DRY_RUN_MODE=false

# Whitelisted IPs (add your management IPs)
WHITELISTED_IPS=127.0.0.1,::1,192.168.1.1,192.168.1.100,192.168.1.150
```

**Save and exit** (Ctrl+X, Y, Enter)

### Step 6: Create Data Directories

```bash
# Create persistent storage directories
sudo mkdir -p /opt/autoshield/data/postgres
sudo mkdir -p /opt/autoshield/logs
sudo mkdir -p /opt/autoshield/backups

# Set ownership
sudo chown -R autoshield:autoshield /opt/autoshield
```

### Step 7: Start AutoShield Services

```bash
# As autoshield user
cd /opt/autoshield

# Pull/build Docker images
docker compose pull
docker compose build

# Start services (without Java backend for now)
docker compose up -d postgres kali-mcp python-ai

# Check status
docker compose ps

# View logs
docker compose logs -f
```

**Expected output**:
```
NAME                    IMAGE                    STATUS              PORTS
autoshield-postgres     postgres:15-alpine       Up (healthy)        5432/tcp
autoshield-kali         autoshield-kali-mcp      Up (healthy)        0.0.0.0:8001->8001/tcp
autoshield-ai           autoshield-python-ai     Up (healthy)        0.0.0.0:8000->8000/tcp
```

### Step 8: Verify Installation

```bash
# Check health endpoints
curl http://localhost:8000/health
curl http://localhost:8001/health

# Expected response (healthy)
{"status":"healthy","mcp_connection":{"connected":true,...}}

# Test from outside LXC (from Proxmox host or another machine)
curl http://192.168.1.150:8000/health
curl http://192.168.1.150:8001/health

# Send test security event
curl -X POST http://192.168.1.150:8000/api/v1/security-event \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "failed_login_attempt",
    "source_ip": "192.168.1.200",
    "severity": "low"
  }'
```

---

## 🌐 Network Configuration

### Container Network Interfaces

```bash
# Inside LXC container
ip addr show

# You should see:
# - eth0: LXC network (e.g., 192.168.1.150)
# - docker0: Docker bridge (172.17.0.1)
# - br-xxxxx: AutoShield network (172.20.0.1)
```

### Port Forwarding (Optional)

If you want to access AutoShield from outside your LAN:

**On Proxmox host firewall**:
```bash
# Allow ports through Proxmox firewall
# Edit /etc/pve/firewall/150.fw

[RULES]
IN ACCEPT -p tcp -dport 8000 -log nolog
IN ACCEPT -p tcp -dport 8001 -log nolog
IN ACCEPT -p tcp -dport 8080 -log nolog

[OPTIONS]
enable: 1
```

**On your router** (for external access):
- Forward port 8000 → 192.168.1.150:8000 (AI API)
- Forward port 8001 → 192.168.1.150:8001 (Kali Tools)
- Forward port 8080 → 192.168.1.150:8080 (Web UI - when ready)

**⚠️ Security Warning**: Only expose if you understand the risks. Use VPN instead for production.

---

## 🔥 Firewall Rules

### LXC Container Firewall (UFW)

```bash
# Inside LXC container
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Allow SSH
sudo ufw allow 22/tcp

# Allow AutoShield services
sudo ufw allow 8000/tcp comment 'AutoShield AI API'
sudo ufw allow 8001/tcp comment 'AutoShield Kali Tools'
sudo ufw allow 8080/tcp comment 'AutoShield Web UI'

# Allow from Proxmox host only (optional, more restrictive)
# sudo ufw allow from 192.168.1.100 to any port 8000 proto tcp
# sudo ufw allow from 192.168.1.100 to any port 8001 proto tcp

# Enable firewall
sudo ufw enable

# Check status
sudo ufw status verbose
```

### Docker Container Networking

Docker containers communicate internally via the `autoshield-network` bridge (172.20.0.0/16). This is isolated from the LXC host network.

**Internal DNS resolution**:
- `postgres` → 172.20.0.2 (database)
- `python-ai` → 172.20.0.3 (AI controller)
- `kali-mcp` → 172.20.0.4 (security tools)
- `java-backend` → 172.20.0.5 (web backend - TODO)

---

## 📊 Monitoring & Maintenance

### System Resources

```bash
# Monitor LXC container resources (from Proxmox host)
pct status 150
pveam available

# Inside LXC, monitor Docker containers
docker stats

# View container resource usage
docker compose top
```

### Log Management

```bash
# View all service logs
docker compose logs

# Follow logs in real-time
docker compose logs -f

# View specific service logs
docker compose logs python-ai
docker compose logs kali-mcp

# View last 100 lines
docker compose logs --tail=100

# Export logs for analysis
docker compose logs --no-color > /opt/autoshield/logs/autoshield-$(date +%Y%m%d).log
```

### Health Checks

```bash
# Create health check script
cat > /opt/autoshield/scripts/health-check.sh <<'EOF'
#!/bin/bash
echo "=== AutoShield Health Check ==="
echo "Timestamp: $(date)"
echo ""

echo "Docker Containers:"
docker compose ps

echo ""
echo "Service Health:"
curl -s http://localhost:8000/health | jq .
curl -s http://localhost:8001/health | jq .

echo ""
echo "Resource Usage:"
docker stats --no-stream

echo ""
echo "Disk Usage:"
df -h /opt/autoshield
EOF

chmod +x /opt/autoshield/scripts/health-check.sh

# Run health check
/opt/autoshield/scripts/health-check.sh
```

### Automatic Restarts

Docker Compose is configured with `restart: unless-stopped`, so containers will:
- ✅ Auto-restart on failure
- ✅ Start on LXC container boot
- ✅ Recover from crashes

**Enable Docker Compose on boot**:
```bash
# Create systemd service
sudo cat > /etc/systemd/system/autoshield.service <<'EOF'
[Unit]
Description=AutoShield Security Platform
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/autoshield
ExecStart=/usr/bin/docker compose up -d
ExecStop=/usr/bin/docker compose down
TimeoutStartSec=0
User=autoshield
Group=autoshield

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable autoshield.service
sudo systemctl start autoshield.service

# Check status
sudo systemctl status autoshield.service
```

---

## 🐛 Troubleshooting

### Issue: LXC Container Won't Start

**Symptoms**: Container fails to start or immediately stops

**Solution**:
```bash
# Check LXC config
pct config 150

# Verify nesting is enabled
grep "nesting=1" /etc/pve/lxc/150.conf

# Check Proxmox logs
journalctl -u pve-container@150.service -n 50

# Try starting with debug
pct start 150 --debug
```

### Issue: Docker Won't Start in LXC

**Symptoms**: `docker: Cannot connect to the Docker daemon`

**Solution**:
```bash
# Inside LXC container
systemctl status docker

# If failed, check kernel modules
lsmod | grep overlay
lsmod | grep br_netfilter

# Restart Docker
systemctl restart docker

# Check for AppArmor issues
dmesg | grep -i apparmor

# If AppArmor blocking, disable in Proxmox host:
# Edit /etc/pve/lxc/150.conf
# Add: lxc.apparmor.profile: unconfined
# pct reboot 150
```

### Issue: Kali Container Can't Scan Network

**Symptoms**: Nmap scans fail with permission errors

**Solution**:
```bash
# Verify container is privileged
docker inspect autoshield-kali | grep -i privileged
# Should show: "Privileged": true

# Check capabilities
docker inspect autoshield-kali | grep -i cap
# Should show: NET_ADMIN, NET_RAW, SYS_ADMIN

# Verify network mode
docker inspect autoshield-kali | grep -i networkmode
# Should show: "bridge"

# Test Nmap manually
docker exec -it autoshield-kali nmap -sn 192.168.1.1
```

### Issue: Services Can't Connect to Each Other

**Symptoms**: Python AI can't connect to Kali MCP

**Solution**:
```bash
# Check Docker network
docker network inspect autoshield_autoshield-network

# Verify all containers are on same network
docker compose ps

# Test connectivity between containers
docker exec autoshield-ai ping -c 3 kali-mcp
docker exec autoshield-ai curl http://kali-mcp:8001/health

# Check DNS resolution
docker exec autoshield-ai nslookup kali-mcp
```

### Issue: High Memory Usage

**Symptoms**: LXC container using too much RAM

**Solution**:
```bash
# Check container limits (from Proxmox host)
pct config 150 | grep memory

# Inside LXC, check Docker memory
docker stats

# Limit container memory in docker-compose.yml
# Add to each service:
#   deploy:
#     resources:
#       limits:
#         memory: 2G

# Restart services
docker compose down
docker compose up -d
```

### Issue: Database Connection Errors

**Symptoms**: Python AI can't connect to PostgreSQL

**Solution**:
```bash
# Check database is running
docker compose ps postgres

# Check database logs
docker compose logs postgres

# Test connection manually
docker exec -it autoshield-postgres psql -U autoshield -d autoshield -c "\l"

# Verify environment variables
docker compose exec python-ai env | grep POSTGRES
```

---

## 💾 Backup & Recovery

### Backup Strategy

**Option 1: Proxmox Snapshots** (Fastest)
```bash
# From Proxmox host
# Create snapshot (entire LXC state)
pct snapshot 150 autoshield-backup-$(date +%Y%m%d) --description "AutoShield backup"

# List snapshots
pct listsnapshot 150

# Restore snapshot
pct rollback 150 autoshield-backup-20251130

# Delete old snapshots
pct delsnapshot 150 autoshield-backup-20251120
```

**Option 2: Docker Volume Backup** (Database only)
```bash
# Inside LXC container
cd /opt/autoshield

# Backup PostgreSQL data
docker compose exec postgres pg_dump -U autoshield autoshield > backups/autoshield-db-$(date +%Y%m%d).sql

# Backup Docker volumes
sudo tar -czf backups/autoshield-volumes-$(date +%Y%m%d).tar.gz data/

# Backup configuration
tar -czf backups/autoshield-config-$(date +%Y%m%d).tar.gz .env docker-compose.yml
```

**Option 3: Full LXC Backup**
```bash
# From Proxmox host
# Backup to Proxmox backup storage
vzdump 150 --storage local --mode snapshot --compress zstd

# Backup files are stored in:
# /var/lib/vz/dump/vzdump-lxc-150-*.tar.zst
```

### Restore Procedures

**Restore from Proxmox Snapshot**:
```bash
# From Proxmox host
pct stop 150
pct rollback 150 autoshield-backup-20251130
pct start 150
```

**Restore Database from SQL Dump**:
```bash
# Inside LXC container
cd /opt/autoshield

# Stop services
docker compose down

# Start only database
docker compose up -d postgres

# Wait for database to be ready
sleep 10

# Restore database
docker compose exec -T postgres psql -U autoshield autoshield < backups/autoshield-db-20251130.sql

# Start all services
docker compose up -d
```

**Restore Full LXC from Backup**:
```bash
# From Proxmox host
# Stop and remove existing container
pct stop 150
pct destroy 150

# Restore from backup file
pct restore 150 /var/lib/vz/dump/vzdump-lxc-150-2025_11_30-12_00_00.tar.zst \
    --storage local-lvm \
    --unprivileged 0

# Start container
pct start 150
```

### Automated Backup Script

```bash
# Create backup script
sudo cat > /opt/autoshield/scripts/backup.sh <<'EOF'
#!/bin/bash
set -e

BACKUP_DIR="/opt/autoshield/backups"
DATE=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=7

echo "=== AutoShield Backup Started: $(date) ==="

# Backup database
echo "Backing up database..."
docker compose exec -T postgres pg_dump -U autoshield autoshield | gzip > "$BACKUP_DIR/db-$DATE.sql.gz"

# Backup configuration
echo "Backing up configuration..."
tar -czf "$BACKUP_DIR/config-$DATE.tar.gz" .env docker-compose.yml

# Backup logs
echo "Backing up logs..."
docker compose logs --no-color > "$BACKUP_DIR/logs-$DATE.log"

# Delete old backups
echo "Cleaning up old backups..."
find "$BACKUP_DIR" -name "*.gz" -mtime +$RETENTION_DAYS -delete
find "$BACKUP_DIR" -name "*.log" -mtime +$RETENTION_DAYS -delete

echo "=== Backup Completed: $(date) ==="
echo "Backup files: $BACKUP_DIR/*-$DATE.*"
EOF

chmod +x /opt/autoshield/scripts/backup.sh

# Test backup
/opt/autoshield/scripts/backup.sh

# Schedule daily backups (cron)
sudo crontab -e -u autoshield
# Add line:
# 0 2 * * * /opt/autoshield/scripts/backup.sh >> /opt/autoshield/logs/backup.log 2>&1
```

---

## 🎓 Best Practices

### 1. Security Hardening

- ✅ Change all default passwords and tokens
- ✅ Use strong authentication tokens (32+ characters)
- ✅ Enable UFW firewall in LXC
- ✅ Whitelist your management IPs
- ✅ Disable root SSH (use autoshield user)
- ✅ Keep LXC and Docker updated
- ✅ Review logs regularly

### 2. Performance Optimization

- ✅ Allocate sufficient CPU cores (4+)
- ✅ Provide adequate RAM (8GB+)
- ✅ Use SSD storage for PostgreSQL
- ✅ Monitor resource usage with `htop` and `docker stats`
- ✅ Implement log rotation
- ✅ Clean old Docker images periodically

### 3. Monitoring

- ✅ Enable Proxmox email alerts
- ✅ Monitor LXC resource graphs in Proxmox UI
- ✅ Set up daily backup cron jobs
- ✅ Review AutoShield logs weekly
- ✅ Test disaster recovery procedures monthly

### 4. Updates

```bash
# Update LXC container
sudo apt update && sudo apt upgrade -y

# Update Docker images
cd /opt/autoshield
docker compose pull
docker compose up -d

# Update AutoShield code (when new version available)
git pull
docker compose build
docker compose up -d
```

---

## 📞 Support & Additional Resources

- **Project Documentation**: `/opt/autoshield/docs/`
- **README**: `/opt/autoshield/README.md`
- **API Reference**: `/opt/autoshield/docs/API.md`
- **Proxmox Wiki**: https://pve.proxmox.com/wiki/Linux_Container
- **Docker Documentation**: https://docs.docker.com/

---

## ✅ Deployment Checklist

Use this checklist to verify your deployment:

- [ ] Proxmox LXC container created (privileged, nesting enabled)
- [ ] Container has static IP assigned
- [ ] Docker Engine installed and running
- [ ] AutoShield files copied to `/opt/autoshield`
- [ ] `.env` file configured with secure passwords
- [ ] Data directories created (`/opt/autoshield/data`)
- [ ] Docker Compose services started
- [ ] Health checks pass (curl http://localhost:8000/health)
- [ ] Services accessible from LAN (curl http://192.168.1.150:8000/health)
- [ ] UFW firewall configured and enabled
- [ ] Systemd service created for auto-start
- [ ] Backup script configured and tested
- [ ] Proxmox snapshot created
- [ ] All default passwords changed
- [ ] Whitelisted IPs configured correctly
- [ ] Test security event processed successfully
- [ ] Logs reviewed for errors

---

**🎉 Congratulations!** Your AutoShield security platform is now deployed in a single Proxmox LXC container with all services running in Docker.

**Next Steps**:
1. Monitor logs for first 24 hours
2. Send test security events to verify functionality
3. Configure Proxmox integration (when Java backend ready)
4. Set up external monitoring (optional)
5. Document your custom configuration

**Deployment Date**: _________________  
**Deployed By**: _________________  
**LXC IP**: _________________  
**Notes**: _________________
