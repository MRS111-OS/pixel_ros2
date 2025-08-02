# Reverse Tunnel Service Setup

This guide provides step-by-step instructions for setting up a reverse SSH tunnel service using systemctl.

## Prerequisites

- SSH access to both local and remote machines
- Root or sudo privileges on the local machine
- SSH key pair for authentication

## Step 1: Copy SSH Keys

Copy the SSH private key to the `.ssh` folder:

```bash
# Create .ssh directory if it doesn't exist
mkdir -p ~/.ssh

# Copy the proxy jumper key to your .ssh directory
cp proxyjumper_tahjzf6z ~/.ssh/

# Set correct permissions for the SSH key
chmod 600 ~/.ssh/proxyjumper_tahjzf6z
```

## Step 2: Copy and Install the Service File

Copy the existing service file to systemd directory:

```bash
# Copy the service file to systemd directory
sudo cp reverse_tunnel.service /etc/systemd/system/

# Make the service file executable
sudo chmod 644 /etc/systemd/system/reverse_tunnel.service
```

The service file contains the following configuration:
```ini
[Unit]
Description=Reverse SSH Tunnel for %i
After=network.target

[Service]
User=%i
ExecStart=/usr/bin/ssh \
  -o "ServerAliveInterval=60" \
  -o "ServerAliveCountMax=3" \
  -o "StrictHostKeyChecking=accept-new" \
  -i /home/%i/.ssh/proxyjumper_tahjzf6z \
  -N -R /PC4:localhost:22 tahjzf6z2@api2.proxypilot.org
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Configuration Details:**
- Uses template service with `%i` for username
- SSH Key: `proxyjumper_tahjzf6z`
- Remote User: `tahjzf6z2@api2.proxypilot.org`
- Tunnel: Forwards local SSH (port 22) to remote socket `/PC4`
- Auto-restart: Service restarts automatically if it fails

## Step 3: Enable and Start the Service

```bash
# Get your current username
USERNAME=$(whoami)

# Reload systemd to recognize the new service
sudo systemctl daemon-reload

# Enable the service for your user (replace $USERNAME with your actual username)
sudo systemctl enable reverse_tunnel@$USERNAME.service

# Start the service immediately
sudo systemctl start reverse_tunnel@$USERNAME.service
```

## Step 4: Check Service Status

```bash
# Check if the service is running
sudo systemctl status reverse_tunnel@$(whoami).service

# View real-time service logs
sudo journalctl -u reverse_tunnel@$(whoami).service -f

# Check if the service is enabled
sudo systemctl is-enabled reverse_tunnel@$(whoami).service

# Check if the service is active
sudo systemctl is-active reverse_tunnel@$(whoami).service
```

## Step 5: Service Management Commands

```bash
# Restart the service
sudo systemctl restart reverse_tunnel@$(whoami).service

# Stop the service
sudo systemctl stop reverse_tunnel@$(whoami).service

# Disable the service (prevent auto-start on boot)
sudo systemctl disable reverse_tunnel@$(whoami).service

# View detailed service logs
sudo journalctl -u reverse_tunnel@$(whoami).service --since "1 hour ago"
```

## Troubleshooting

### Common Issues and Solutions:

1. **Permission denied for SSH key:**
   ```bash
   chmod 600 ~/.ssh/proxyjumper_tahjzf6z
   ```

2. **Service fails to start:**
   ```bash
   # Check logs for errors
   sudo journalctl -u reverse_tunnel@$(whoami).service -n 20
   ```

3. **Connection refused:**
   - Verify remote host is reachable
   - Check if remote socket is available
   - Ensure SSH service is running on remote host

4. **Service stops unexpectedly:**
   - Check network connectivity
   - Verify SSH key authentication works manually:
   ```bash
   ssh -i ~/.ssh/proxyjumper_tahjzf6z tahjzf6z2@api2.proxypilot.org
   ```

### Test the Tunnel Manually:

Before setting up the service, test the tunnel manually:

```bash
ssh -o "ServerAliveInterval=60" \
    -o "ServerAliveCountMax=3" \
    -o "StrictHostKeyChecking=accept-new" \
    -i ~/.ssh/proxyjumper_tahjzf6z \
    -N -R /PC4:localhost:22 tahjzf6z2@api2.proxypilot.org
```

### Example Configuration:

The current setup forwards local SSH (port 22) to remote socket `/PC4`:

```ini
[Unit]
Description=Reverse SSH Tunnel for %i
After=network.target

[Service]
User=%i
ExecStart=/usr/bin/ssh \
  -o "ServerAliveInterval=60" \
  -o "ServerAliveCountMax=3" \
  -o "StrictHostKeyChecking=accept-new" \
  -i /home/%i/.ssh/proxyjumper_tahjzf6z \
  -N -R /PC4:localhost:22 tahjzf6z2@api2.proxypilot.org
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

## Security Considerations

1. Use key-based authentication instead of passwords
2. Restrict SSH key permissions (chmod 600)
3. Consider using SSH config file for better organization
4. Monitor service logs regularly
5. Use strong SSH keys (RSA 2048-bit minimum or Ed25519)

## Advanced Configuration

### Using SSH Config File:

Create `~/.ssh/config`:

```
Host reverse-tunnel
    HostName api2.proxypilot.org
    User tahjzf6z2
    IdentityFile ~/.ssh/proxyjumper_tahjzf6z
    ServerAliveInterval 60
    ServerAliveCountMax 3
    StrictHostKeyChecking accept-new
```

Then modify the service ExecStart:

```ini
ExecStart=/usr/bin/ssh -N -R /PC4:localhost:22 reverse-tunnel
```

## Quick Setup (All-in-One)

For users who want to run all commands at once:

```bash
# Run all setup commands at once
USERNAME=$(whoami)
mkdir -p ~/.ssh
cp /Volumes/Code/MomentumRobotics/titan_robot/shell_scripts/proxyjumper_tahjzf6z ~/.ssh/
chmod 600 ~/.ssh/proxyjumper_tahjzf6z
sudo cp /Volumes/Code/MomentumRobotics/titan_robot/shell_scripts/reverse_tunnel.service /etc/systemd/system/
sudo chmod 644 /etc/systemd/system/reverse_tunnel.service
sudo systemctl daemon-reload
sudo systemctl enable reverse_tunnel@$USERNAME.service
sudo systemctl start reverse_tunnel@$USERNAME.service
sudo systemctl status reverse_tunnel@$USERNAME.service
```

This setup ensures your reverse tunnel service will automatically start on boot and restart if it fails, providing a reliable connection to your remote system.
