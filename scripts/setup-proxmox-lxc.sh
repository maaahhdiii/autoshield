#!/bin/bash
################################################################################
# AutoShield - Proxmox LXC Container Setup Script
# 
# This script automates the creation of a Proxmox LXC container for AutoShield
# Run this on your Proxmox host as root.
#
# Usage: ./setup-proxmox-lxc.sh
################################################################################

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration (modify these as needed)
CTID=150                          # LXC Container ID
HOSTNAME="autoshield-main"        # Container hostname
STORAGE="local-lvm"               # Storage for container
TEMPLATE_STORAGE="local"          # Storage for templates
DISK_SIZE=50                      # Disk size in GB
MEMORY=8192                       # RAM in MB
SWAP=2048                         # Swap in MB
CORES=4                           # CPU cores
PASSWORD=""                       # Root password (leave empty to prompt)
NETWORK_BRIDGE="vmbr0"            # Network bridge
IP_ADDRESS="192.168.1.150/24"     # Static IP (modify for your network)
GATEWAY="192.168.1.1"             # Network gateway
NAMESERVER="8.8.8.8"              # DNS server

################################################################################
# Functions
################################################################################

print_header() {
    echo -e "${BLUE}"
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║         AutoShield Proxmox LXC Setup Script v1.0              ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_root() {
    if [ "$EUID" -ne 0 ]; then
        print_error "This script must be run as root"
        exit 1
    fi
}

check_proxmox() {
    if ! command -v pct &> /dev/null; then
        print_error "This script must be run on a Proxmox host"
        exit 1
    fi
    print_info "Proxmox VE detected"
}

download_template() {
    print_info "Checking for Ubuntu 22.04 template..."
    
    # Update template list
    pveam update
    
    # Check if template exists
    TEMPLATE=$(pveam available | grep ubuntu-22.04-standard | head -n1 | awk '{print $2}')
    
    if [ -z "$TEMPLATE" ]; then
        print_error "Ubuntu 22.04 template not found"
        exit 1
    fi
    
    print_info "Found template: $TEMPLATE"
    
    # Check if already downloaded
    if pveam list $TEMPLATE_STORAGE | grep -q "$TEMPLATE"; then
        print_info "Template already downloaded"
    else
        print_info "Downloading Ubuntu 22.04 template..."
        pveam download $TEMPLATE_STORAGE $TEMPLATE
    fi
    
    TEMPLATE_PATH="$TEMPLATE_STORAGE:vztmpl/$TEMPLATE"
}

check_ctid() {
    if pct status $CTID &>/dev/null; then
        print_error "Container $CTID already exists"
        read -p "Do you want to destroy and recreate it? (yes/no): " -r
        if [[ $REPLY =~ ^[Yy]es$ ]]; then
            print_warning "Stopping and destroying container $CTID..."
            pct stop $CTID 2>/dev/null || true
            sleep 2
            pct destroy $CTID
            print_info "Container $CTID destroyed"
        else
            print_error "Aborted by user"
            exit 1
        fi
    fi
}

get_password() {
    if [ -z "$PASSWORD" ]; then
        read -s -p "Enter root password for container: " PASSWORD
        echo ""
        read -s -p "Confirm password: " PASSWORD_CONFIRM
        echo ""
        
        if [ "$PASSWORD" != "$PASSWORD_CONFIRM" ]; then
            print_error "Passwords do not match"
            exit 1
        fi
    fi
}

create_container() {
    print_info "Creating LXC container $CTID..."
    
    pct create $CTID $TEMPLATE_PATH \
        --hostname $HOSTNAME \
        --storage $STORAGE \
        --rootfs $STORAGE:$DISK_SIZE \
        --memory $MEMORY \
        --swap $SWAP \
        --cores $CORES \
        --password "$PASSWORD" \
        --net0 name=eth0,bridge=$NETWORK_BRIDGE,ip=$IP_ADDRESS,gw=$GATEWAY \
        --nameserver $NAMESERVER \
        --unprivileged 0 \
        --features nesting=1,keyctl=1 \
        --onboot 1 \
        --ostype ubuntu
    
    print_info "Container $CTID created successfully"
}

configure_container() {
    print_info "Configuring container for Docker..."
    
    # Get config file path
    CONFIG_FILE="/etc/pve/lxc/${CTID}.conf"
    
    # Backup original config
    cp $CONFIG_FILE ${CONFIG_FILE}.backup
    
    # Add Docker-specific configuration
    cat >> $CONFIG_FILE <<EOF

# Docker and AutoShield specific configuration
lxc.apparmor.profile: unconfined
lxc.cgroup2.devices.allow: a
lxc.cap.drop:
lxc.mount.auto: proc:rw sys:rw cgroup:rw

# Network capabilities for Kali tools
lxc.cgroup2.devices.allow: c 10:200 rwm
lxc.cgroup2.devices.allow: b 7:* rwm
lxc.cgroup2.devices.allow: c 10:237 rwm
EOF
    
    print_info "Container configuration updated"
}

start_container() {
    print_info "Starting container..."
    pct start $CTID
    
    # Wait for container to be fully started
    sleep 5
    
    if pct status $CTID | grep -q "running"; then
        print_info "Container started successfully"
    else
        print_error "Failed to start container"
        exit 1
    fi
}

install_docker() {
    print_info "Installing Docker in container..."
    
    # Execute commands in container
    pct exec $CTID -- bash -c "
        set -e
        
        # Update system
        apt-get update
        apt-get upgrade -y
        
        # Install prerequisites
        apt-get install -y \
            ca-certificates \
            curl \
            gnupg \
            lsb-release \
            git \
            nano \
            htop \
            net-tools \
            ufw \
            sudo
        
        # Add Docker's official GPG key
        mkdir -p /etc/apt/keyrings
        curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
        
        # Set up Docker repository
        echo \
          \"deb [arch=\$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
          \$(lsb_release -cs) stable\" | tee /etc/apt/sources.list.d/docker.list > /dev/null
        
        # Install Docker
        apt-get update
        apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
        
        # Configure Docker
        mkdir -p /etc/docker
        cat > /etc/docker/daemon.json <<'DOCKEREOF'
{
  \"log-driver\": \"json-file\",
  \"log-opts\": {
    \"max-size\": \"10m\",
    \"max-file\": \"3\"
  },
  \"storage-driver\": \"overlay2\",
  \"live-restore\": true,
  \"userland-proxy\": false
}
DOCKEREOF
        
        # Restart Docker
        systemctl restart docker
        systemctl enable docker
        
        # Create autoshield user
        useradd -m -s /bin/bash autoshield
        usermod -aG docker autoshield
        usermod -aG sudo autoshield
        echo 'autoshield ALL=(ALL) NOPASSWD:ALL' > /etc/sudoers.d/autoshield
        chmod 440 /etc/sudoers.d/autoshield
        
        # Create project directory
        mkdir -p /opt/autoshield/data/postgres
        mkdir -p /opt/autoshield/logs
        mkdir -p /opt/autoshield/backups
        mkdir -p /opt/autoshield/scripts
        chown -R autoshield:autoshield /opt/autoshield
        
        echo 'Docker installation completed'
    "
    
    print_info "Docker installed successfully"
}

configure_firewall() {
    print_info "Configuring UFW firewall..."
    
    pct exec $CTID -- bash -c "
        ufw default deny incoming
        ufw default allow outgoing
        ufw allow 22/tcp comment 'SSH'
        ufw allow 8000/tcp comment 'AutoShield AI API'
        ufw allow 8001/tcp comment 'AutoShield Kali Tools'
        ufw allow 8080/tcp comment 'AutoShield Web UI'
        ufw --force enable
    "
    
    print_info "Firewall configured"
}

print_summary() {
    echo ""
    echo -e "${GREEN}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║              Container Setup Complete!                         ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${BLUE}Container Details:${NC}"
    echo "  CT ID:       $CTID"
    echo "  Hostname:    $HOSTNAME"
    echo "  IP Address:  $IP_ADDRESS"
    echo "  Memory:      ${MEMORY}MB"
    echo "  Cores:       $CORES"
    echo "  Storage:     ${DISK_SIZE}GB"
    echo ""
    echo -e "${BLUE}Next Steps:${NC}"
    echo "  1. Enter the container:"
    echo "     ${GREEN}pct enter $CTID${NC}"
    echo ""
    echo "  2. Switch to autoshield user:"
    echo "     ${GREEN}su - autoshield${NC}"
    echo ""
    echo "  3. Copy AutoShield files to /opt/autoshield/"
    echo "     ${GREEN}scp -r /path/to/autoshield/* autoshield@${IP_ADDRESS%/*}:/opt/autoshield/${NC}"
    echo ""
    echo "  4. Configure environment:"
    echo "     ${GREEN}cd /opt/autoshield${NC}"
    echo "     ${GREEN}cp .env.example .env${NC}"
    echo "     ${GREEN}nano .env${NC}"
    echo ""
    echo "  5. Start AutoShield services:"
    echo "     ${GREEN}docker compose up -d${NC}"
    echo ""
    echo "  6. Check status:"
    echo "     ${GREEN}docker compose ps${NC}"
    echo "     ${GREEN}curl http://localhost:8000/health${NC}"
    echo ""
    echo -e "${YELLOW}Documentation:${NC}"
    echo "  - Full guide: /opt/autoshield/docs/PROXMOX_DEPLOYMENT.md"
    echo "  - API docs:   /opt/autoshield/docs/API.md"
    echo ""
}

################################################################################
# Main Execution
################################################################################

print_header

# Pre-flight checks
check_root
check_proxmox

# User confirmation
echo -e "${YELLOW}This script will create a new LXC container with the following configuration:${NC}"
echo "  CT ID:       $CTID"
echo "  Hostname:    $HOSTNAME"
echo "  IP Address:  $IP_ADDRESS"
echo "  Memory:      ${MEMORY}MB"
echo "  Cores:       $CORES"
echo "  Disk:        ${DISK_SIZE}GB"
echo ""
read -p "Do you want to continue? (yes/no): " -r
if [[ ! $REPLY =~ ^[Yy]es$ ]]; then
    print_error "Aborted by user"
    exit 0
fi

# Execute setup steps
print_info "Starting AutoShield LXC setup..."
echo ""

check_ctid
download_template
get_password
create_container
configure_container
start_container
install_docker
configure_firewall

print_summary

print_info "Setup completed successfully!"
echo ""

exit 0
