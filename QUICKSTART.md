# AutoShield Quick Start Guide

Get AutoShield running in your Proxmox home lab in **under 30 minutes**.

---

## 🎯 Prerequisites Checklist

Before starting, ensure you have:

- [ ] **Proxmox VE** 7.x or 8.x installed
- [ ] **Network access** to Proxmox web UI and SSH
- [ ] **Static IP available** for AutoShield (e.g., 192.168.1.150)
- [ ] **4 CPU cores** and **8GB RAM** available
- [ ] **50GB disk space** available
- [ ] **Proxmox API token** created (optional, for integration)

---

## 🚀 Method 1: Automated Setup (Easiest)

### Step 1: Download Setup Script

```bash
# SSH into your Proxmox host
ssh root@your-proxmox-ip

# Download the automated setup script
wget https://raw.githubusercontent.com/maaahhdiii/autoshield/main/scripts/setup-proxmox-lxc.sh

# Or copy from your local files
# scp scripts/setup-proxmox-lxc.sh root@proxmox-ip:/root/
```

### Step 2: Run Setup Script

```bash
# Make executable
chmod +x setup-proxmox-lxc.sh

# Run the script
./setup-proxmox-lxc.sh
```

**The script will**:
- ✅ Download Ubuntu 22.04 LXC template
- ✅ Create privileged container (CT ID 150)
- ✅ Install Docker Engine
- ✅ Configure container for Docker and security tools
- ✅ Set up firewall rules
- ✅ Create autoshield user

**Duration**: ~10 minutes

### Step 3: Deploy AutoShield

```bash
# Enter the container
pct enter 150

# Switch to autoshield user
su - autoshield

# Navigate to project directory
cd /opt/autoshield
```

Now copy your AutoShield files:

**Option A: From development machine**:
```bash
# On your dev machine (Windows PowerShell)
scp -r d:\autoshild\* autoshield@192.168.1.150:/opt/autoshield/

# Or use WinSCP / FileZilla
```

**Option B: Clone from Git**:
```bash
# Inside LXC container as autoshield user
cd /opt/autoshield
git clone https://github.com/maaahhdiii/autoshield.git .
```

### Step 4: Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit configuration
nano .env
```

**Minimal required changes**:
```bash
# Generate secure passwords
POSTGRES_PASSWORD=<generate-strong-password>
MCP_AUTH_TOKEN=<generate-32-char-token>

# Your network settings
ALLOWED_IP_RANGES=192.168.0.0/16

# Whitelist your management IPs
WHITELISTED_IPS=127.0.0.1,192.168.1.1,192.168.1.150

# Optional: Proxmox integration
PROXMOX_API_URL=https://192.168.1.100:8006
PROXMOX_TOKEN_ID=autoshield@pam!monitoring
PROXMOX_TOKEN_SECRET=<your-token-secret>
```

**Save**: Ctrl+X, Y, Enter

### Step 5: Start Services

```bash
# Build and start Docker containers
docker compose up -d postgres kali-mcp python-ai

# Wait for services to start (30 seconds)
sleep 30

# Check status
docker compose ps
```

**Expected output**:
```
NAME                 STATUS              PORTS
autoshield-postgres  Up (healthy)        5432/tcp
autoshield-kali      Up (healthy)        0.0.0.0:8001->8001/tcp
autoshield-ai        Up (healthy)        0.0.0.0:8000->8000/tcp
```

### Step 6: Verify Installation

```bash
# Check health endpoints
curl http://localhost:8000/health
curl http://localhost:8001/health

# Test from outside container (from your PC)
curl http://192.168.1.150:8000/health
```

**Expected response**:
```json
{
  "status": "healthy",
  "mcp_connection": {
    "connected": true,
    "available_tools": 7
  }
}
```

### Step 7: Send Test Security Event

```bash
# Send a test event
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

**Expected response**:
```json
{
  "success": true,
  "threat_score": 45,
  "actions_taken": [
    {
      "success": true,
      "action_taken": "nmap_quick_scan",
      "result": "{...scan results...}"
    }
  ]
}
```

---

## 🎉 Success! AutoShield is Running

Your security platform is now operational:

- **AI Controller**: http://192.168.1.150:8000
- **Kali Tools**: http://192.168.1.150:8001
- **Web UI**: http://192.168.1.150:8080 (TODO - Java backend needed)

---

## 📋 Post-Installation Tasks

### 1. Enable Auto-Start

```bash
# Create systemd service for auto-start on boot
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
User=autoshield
Group=autoshield

[Install]
WantedBy=multi-user.target
EOF

# Enable service
sudo systemctl daemon-reload
sudo systemctl enable autoshield.service
sudo systemctl start autoshield.service
```

### 2. Set Up Backups

```bash
# Create backup script
cat > /opt/autoshield/scripts/backup.sh <<'EOF'
#!/bin/bash
BACKUP_DIR="/opt/autoshield/backups"
DATE=$(date +%Y%m%d_%H%M%S)

# Backup database
docker compose exec -T postgres pg_dump -U autoshield autoshield | gzip > "$BACKUP_DIR/db-$DATE.sql.gz"

# Backup configuration
tar -czf "$BACKUP_DIR/config-$DATE.tar.gz" .env docker-compose.yml

# Clean old backups (keep 7 days)
find "$BACKUP_DIR" -name "*.gz" -mtime +7 -delete
EOF

chmod +x /opt/autoshield/scripts/backup.sh

# Schedule daily backups
crontab -e
# Add line:
# 0 2 * * * /opt/autoshield/scripts/backup.sh
```

### 3. Configure Proxmox Snapshots

```bash
# From Proxmox host, create weekly snapshots
# Add to cron: crontab -e

# 0 3 * * 0 pct snapshot 150 autoshield-weekly-$(date +\%Y\%m\%d)
```

### 4. Monitor Logs

```bash
# View live logs
docker compose logs -f

# View last 100 lines
docker compose logs --tail=100

# View specific service
docker compose logs python-ai
```

---

## 🔒 Security Hardening (Recommended)

### 1. Generate Strong Tokens

```bash
# Generate secure MCP token (32 characters)
openssl rand -hex 16

# Update .env file
nano .env
# Set MCP_AUTH_TOKEN=<generated-token>

# Restart services
docker compose restart
```

### 2. Configure Firewall

```bash
# Verify UFW is active
sudo ufw status

# Restrict access to specific IPs (optional)
sudo ufw delete allow 8000/tcp
sudo ufw delete allow 8001/tcp
sudo ufw allow from 192.168.1.0/24 to any port 8000 proto tcp
sudo ufw allow from 192.168.1.0/24 to any port 8001 proto tcp
sudo ufw reload
```

### 3. Disable Root SSH (Optional)

```bash
# Edit SSH config
sudo nano /etc/ssh/sshd_config

# Change: PermitRootLogin no

# Restart SSH
sudo systemctl restart sshd
```

---

## 🛠️ Common Operations

### Start/Stop Services

```bash
# Stop all services
docker compose down

# Start services
docker compose up -d

# Restart specific service
docker compose restart python-ai

# View status
docker compose ps
```

### Update AutoShield

```bash
# Pull latest changes
cd /opt/autoshield
git pull

# Rebuild containers
docker compose build

# Restart services
docker compose down
docker compose up -d
```

### View Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f python-ai

# Last N lines
docker compose logs --tail=50 kali-mcp
```

### Enter Container

```bash
# Enter Python AI container
docker exec -it autoshield-ai bash

# Enter Kali container
docker exec -it autoshield-kali bash

# Enter as root
docker exec -it -u root autoshield-ai bash
```

---

## 🐛 Troubleshooting

### Issue: Services Won't Start

```bash
# Check Docker is running
systemctl status docker

# Check logs for errors
docker compose logs

# Verify configuration
docker compose config
```

### Issue: Can't Access from Network

```bash
# Check firewall
sudo ufw status

# Test from inside container first
curl http://localhost:8000/health

# Check if ports are bound
netstat -tulpn | grep 8000
```

### Issue: MCP Connection Failed

```bash
# Check Kali container is running
docker compose ps kali-mcp

# Check Kali logs
docker compose logs kali-mcp

# Verify token matches
grep MCP_AUTH_TOKEN .env

# Restart services in order
docker compose restart kali-mcp
sleep 5
docker compose restart python-ai
```

### Issue: Database Connection Error

```bash
# Check database is running
docker compose ps postgres

# Check database logs
docker compose logs postgres

# Test connection
docker compose exec postgres psql -U autoshield -d autoshield -c "\l"
```

---

## 📞 Getting Help

If you encounter issues:

1. **Check logs**: `docker compose logs`
2. **Review documentation**: `/opt/autoshield/docs/`
3. **Verify configuration**: Check `.env` file
4. **Check health**: `curl http://localhost:8000/health`
5. **Restart services**: `docker compose restart`

**Detailed guides**:
- Full deployment guide: `docs/PROXMOX_DEPLOYMENT.md`
- API documentation: `docs/API.md`
- Installation guide: `docs/INSTALLATION.md`

---

## ✅ Next Steps

Now that AutoShield is running:

1. **Test threat detection**: Send security events via API
2. **Configure whitelists**: Add your trusted IPs
3. **Set up monitoring**: Review logs daily
4. **Create backups**: Schedule automated backups
5. **Integrate with Proxmox**: Configure API tokens (when Java backend ready)

---

## 🎓 What You've Accomplished

✅ Created a privileged LXC container  
✅ Installed Docker Engine  
✅ Deployed AutoShield with 3 services  
✅ Configured networking and firewall  
✅ Verified health endpoints  
✅ Sent test security event  

**Your home lab is now protected by intelligent security automation!** 🛡️

---

## 📊 Resource Usage

Typical resource consumption:

- **CPU**: 5-10% idle, up to 50% during scans
- **RAM**: 2-3GB total (postgres: 500MB, python-ai: 200MB, kali: 1.5GB)
- **Disk**: 5-10GB (depends on logs and database)
- **Network**: Minimal when idle, spikes during scans

Monitor with: `docker stats`

---

**Deployment Date**: _______________  
**LXC IP**: _______________  
**Version**: 2.0.0  

**🎉 Congratulations on deploying AutoShield!**
