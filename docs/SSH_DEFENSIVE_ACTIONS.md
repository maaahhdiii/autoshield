# SSH Command Execution - Defensive Actions

AutoShield AI can execute defensive commands on the server via SSH when critical threats are detected.

## Overview

The SSH executor allows the AI to:
- Block/unblock IPs via iptables
- Kill suspicious user sessions
- Disable/enable user accounts
- Restart/stop system services
- Emergency shutdown/reboot
- Flush firewall rules
- Execute custom commands

## Configuration

Add to `.env` file:

```bash
# SSH Configuration
SSH_HOST=localhost           # localhost for same LXC, or remote IP
SSH_PORT=22
SSH_USERNAME=root

# Use either password OR key file
SSH_PASSWORD=your_password
# OR
SSH_KEY_FILE=/root/.ssh/id_rsa

SSH_TIMEOUT=10
```

## Setup SSH Key Authentication (Recommended)

### 1. Generate SSH key inside container:
```bash
ssh-keygen -t rsa -b 4096 -f /root/.ssh/id_rsa -N ""
```

### 2. Add public key to authorized_keys:
```bash
cat /root/.ssh/id_rsa.pub >> /root/.ssh/authorized_keys
chmod 600 /root/.ssh/authorized_keys
chmod 700 /root/.ssh
```

### 3. Test connection:
```bash
ssh -i /root/.ssh/id_rsa root@localhost
```

### 4. Update .env:
```bash
SSH_HOST=localhost
SSH_PORT=22
SSH_USERNAME=root
SSH_KEY_FILE=/root/.ssh/id_rsa
# No password needed
```

## API Endpoints

### Emergency Actions

#### 1. Emergency Shutdown
```bash
POST /api/v1/defense/shutdown?delay=1
```
Shuts down the system in specified minutes (nuclear option).

**Use case:** Critical breach detected, system compromised

#### 2. Emergency Reboot
```bash
POST /api/v1/defense/reboot?delay=1
```
Reboots the system in specified minutes.

**Use case:** Need to clear memory, restart services

#### 3. Cancel Shutdown
```bash
POST /api/v1/defense/cancel-shutdown
```
Cancels pending shutdown/reboot.

### IP Blocking

#### 4. Block IP via SSH/iptables
```bash
POST /api/v1/defense/block-ip-ssh
Content-Type: application/json

{
  "ip_address": "192.168.1.100"
}
```

Alternative to MCP firewall blocking. Uses iptables directly.

#### 5. Unblock IP
```bash
POST /api/v1/defense/unblock-ip-ssh?ip_address=192.168.1.100
```

### User Account Actions

#### 6. Kill User Sessions
```bash
POST /api/v1/defense/kill-user-sessions?username=suspicious_user
```

Terminates all active sessions for a user.

**Use case:** Compromised account, suspicious activity

#### 7. Disable User Account
```bash
POST /api/v1/defense/disable-user?username=suspicious_user
```

Locks the account and kills all sessions.

**Use case:** Confirmed account compromise

#### 8. Enable User Account
```bash
POST /api/v1/defense/enable-user?username=user
```

Re-enables a previously disabled account.

### Service Management

#### 9. Restart Service
```bash
POST /api/v1/defense/restart-service?service_name=sshd
```

Restarts a systemd service.

**Use case:** Service behaving abnormally, needs refresh

#### 10. Stop Service
```bash
POST /api/v1/defense/stop-service?service_name=apache2
```

Stops a running service.

**Use case:** Vulnerable service being exploited

### Firewall Management

#### 11. Flush All Firewall Rules
```bash
POST /api/v1/defense/flush-firewall
```

**⚠️ CAUTION:** Removes ALL firewall rules.

**Use case:** Locked yourself out, emergency access needed

### System Monitoring

#### 12. Get Active Connections
```bash
GET /api/v1/system/connections
```

Returns output of `ss -tunap` showing all network connections.

#### 13. Get System Load
```bash
GET /api/v1/system/load
```

Returns system uptime, memory, and disk usage.

### Custom Commands

#### 14. Execute Custom SSH Command
```bash
POST /api/v1/ssh/execute?command=ls%20-la&use_sudo=true
```

**⚠️ USE WITH EXTREME CAUTION**

Executes any SSH command. Requires admin privileges.

## Automatic Defensive Actions

The AI automatically triggers SSH actions based on threat scores:

### Threat Score >= 90
- Double-blocks IP via both MCP firewall AND SSH/iptables
- Provides redundant blocking

### Threat Score >= 95
- Kills user sessions if account compromise detected
- Disables compromised user accounts

### Threat Score >= 98
- Raises critical alert
- Recommends manual review for potential shutdown
- Does NOT auto-shutdown (requires manual call)

## Examples

### Example 1: Block Attacking IP
```bash
curl -X POST http://localhost:8000/api/v1/defense/block-ip-ssh \
  -H "Content-Type: application/json" \
  -d '{"ip_address": "10.0.0.50"}'
```

Response:
```json
{
  "success": true,
  "message": "IP 10.0.0.50 blocked via iptables",
  "result": {
    "action": "block_ip",
    "ip": "10.0.0.50",
    "success": true
  }
}
```

### Example 2: Emergency Shutdown
```bash
curl -X POST "http://localhost:8000/api/v1/defense/shutdown?delay=2"
```

Response:
```json
{
  "success": true,
  "message": "System shutdown scheduled in 2 minute(s)",
  "result": {
    "action": "shutdown_system",
    "delay_minutes": 2,
    "success": true
  },
  "correlation_id": "abc-123"
}
```

### Example 3: Kill Compromised User
```bash
curl -X POST "http://localhost:8000/api/v1/defense/kill-user-sessions?username=hacker"
```

### Example 4: Check Active Connections
```bash
curl http://localhost:8000/api/v1/system/connections
```

## Security Considerations

### 1. SSH Access
- Use SSH keys instead of passwords
- Restrict SSH to localhost only if possible
- Use `root` user (required for iptables, user management)

### 2. Firewall Rules
```bash
# Allow SSH from LXC internal network only
ufw allow from 172.20.0.0/16 to any port 22
```

### 3. Audit Logging
All SSH commands are logged:
- Python AI logs: `/var/log/autoshield/ai.log`
- System logs: `/var/log/auth.log`
- Audit: `journalctl -u autoshield-ai`

### 4. Dry Run Mode
Test commands without executing:
```bash
DRY_RUN_MODE=true
```

### 5. Whitelisting
Always whitelist:
- Localhost (127.0.0.1)
- LXC container IP
- Proxmox host IP
- Your admin workstation

### 6. Manual Override Required
Emergency shutdown requires **manual API call**. AI will NOT auto-shutdown even at score 100.

Rationale: Prevents false positives from causing service disruption.

## Testing

### Test SSH Connection
```bash
docker exec -it autoshield-ai python3 -c "
from ssh_executor import get_executor
executor = get_executor()
if executor.connect():
    print('✅ SSH connection successful')
    result = executor.execute_command('whoami')
    print(f'Username: {result[\"stdout\"]}')
    executor.disconnect()
else:
    print('❌ SSH connection failed')
"
```

### Test Defensive Actions
```bash
docker exec -it autoshield-ai python3 -c "
from ssh_executor import get_defensive_actions
actions = get_defensive_actions()

# Test system load
result = actions.get_system_load()
print(result)
"
```

## Troubleshooting

### SSH Connection Failed
1. Check SSH service: `systemctl status sshd`
2. Verify credentials in `.env`
3. Test manual SSH: `ssh root@localhost`
4. Check firewall: `ufw status`
5. Review logs: `journalctl -u sshd -f`

### Permission Denied
- Ensure using `root` user
- Check SSH key permissions: `ls -la /root/.ssh/`
- Verify authorized_keys: `cat /root/.ssh/authorized_keys`

### Commands Not Executing
- Check `DRY_RUN_MODE=false`
- Verify user has sudo privileges
- Check command syntax
- Review Python AI logs

### Iptables Rules Not Persisting
```bash
# Install iptables-persistent
apt-get install iptables-persistent

# Save rules
iptables-save > /etc/iptables/rules.v4
ip6tables-save > /etc/iptables/rules.v6
```

## Production Checklist

- [ ] SSH key authentication configured
- [ ] Password auth disabled (or very strong password)
- [ ] Whitelisted IPs configured
- [ ] Dry run mode tested all actions
- [ ] Emergency shutdown tested with long delay
- [ ] Firewall rules persistence configured
- [ ] Logging and monitoring verified
- [ ] Manual override procedures documented
- [ ] Incident response plan includes SSH actions
- [ ] Backup access method available (console)

## License

MIT License - See LICENSE file
