
# 🛰️ Remote RDP Access via SSH Tunnel with Proxy Jumper

This document outlines the complete working setup to access a remote Ubuntu machine's desktop (via `xrdp`) through an SSH reverse tunnel using a **jump server**. It supports both same-network and remote access cases.

---

## ✅ Part A: Configure the Host (Ubuntu RDP Server)

### 1. Install xrdp

```bash
sudo apt update
sudo apt install xrdp
```

### 2. Enable and start xrdp

```bash
sudo systemctl enable xrdp
sudo systemctl start xrdp
```

### 3. Allow port 3389 in the firewall

```bash
sudo ufw allow 3389/tcp
```

### 4. Verify RDP is listening

```bash
sudo ss -tuln | grep 3389
```

Expected output:

```
LISTEN 0 128 *:3389 *:*
```

---

## ✅ Part B: Optional Local LAN Access

If both client and server are on the **same network**:

- Open any RDP client (e.g., Microsoft Remote Desktop)
- Connect to:

  ```
  <remote_machine_ip>:3389
  ```

---

## ✅ Part C: Remote Access via Proxy Jumper

### 🔁 Architecture

```
[Client Mac/PC] --> [Proxy Server] --> [Remote Ubuntu Machine with xrdp]
```

---

### 1. Prepare Files on Host (Remote Ubuntu Machine)

Copy the files:

```bash
cp proxyjumper_key reverse_ssh.conf start_reverse_ssh.sh ~/.ssh/
chmod 700 ~/.ssh/proxyjumper_key ~/.ssh/reverse_ssh.conf ~/.ssh/start_reverse_ssh.sh
chown $USER:$USER ~/.ssh/proxyjumper_key ~/.ssh/reverse_ssh.conf ~/.ssh/start_reverse_ssh.sh
```

#### Example content of `reverse_ssh.conf`:

```conf
PROXY_USER=tahjzf6z
PROXY_HOST=api2.proxypilot.org
IDENTIFIER=NUC1_22
```

---

### 2. Install Reverse Tunnel as a Systemd Service

#### Step 1: Place service file

```bash
sudo cp reverse_tunnel@.service /etc/systemd/system/reverse_tunnel@.service
```

#### Step 2: Reload and enable systemd service

```bash
sudo systemctl daemon-reload
sudo systemctl enable reverse_tunnel@$(whoami).service
sudo systemctl start reverse_tunnel@$(whoami).service
```

✅ This will:

- Automatically use the current username
- Run the script from `~/.ssh/start_reverse_ssh.sh`
- Auto-restart if the tunnel drops

---

### 3. Log File and Monitoring

The log file is located at:

```bash
~/reverse_tunnel_debug.log
```

To view logs:

```bash
tail -f ~/reverse_tunnel_debug.log
```

📝 The log rotates automatically when it exceeds 1MB. You'll see:

- Service started timestamp
- `ssh` debug logs
- Periodic keepalive messages every 5 minutes
- Shutdown timestamp

---

### 4. At Client Side (Mac/Windows)

Run the following from your local machine:

```bash
ssh -v -o ProxyCommand="ssh -i ~/.ssh/proxyjumper_key tahjzf6z@api2.proxypilot.org -W /NUC1_22" \
    -L 3390:localhost:3389 user@localhost
```

🧠 This forwards:

```
localhost:3390 (your Mac/PC) → remote:3389 (RDP port)
```

---

### 5. Connect using Microsoft Remote Desktop

Use **Microsoft Remote Desktop** (or any RDP client):

- **PC name**: `127.0.0.1:3390`
- **Username**: your Ubuntu username
- **Password**: your Ubuntu login password

If needed, enable XFCE:

```bash
echo "startxfce4" > ~/.xsession
```

---

## 🧪 Summary of Key Commands

| Task                          | Command                                         |
|-------------------------------|-------------------------------------------------|
| Enable xrdp                   | `sudo systemctl enable xrdp`                   |
| Start RDP                     | `sudo systemctl start xrdp`                    |
| Check port 3389               | `sudo ss -tuln | grep 3389`                    |
| Copy and set permissions      | `chmod 700 ~/.ssh/*`                           |
| Enable reverse tunnel service | `sudo systemctl enable reverse_tunnel@user`    |
| Start reverse tunnel service  | `sudo systemctl start reverse_tunnel@user`     |
| View tunnel logs              | `tail -f ~/reverse_tunnel_debug.log`           |

---

## ✅ Uninstall Instructions

To stop and disable the service:

```bash
sudo systemctl stop reverse_tunnel@$(whoami).service
sudo systemctl disable reverse_tunnel@$(whoami).service
```

To remove the service completely:

```bash
sudo rm /etc/systemd/system/reverse_tunnel@.service
sudo systemctl daemon-reload
```

---

## 🛠 Troubleshooting

| Problem                        | Solution                                          |
|-------------------------------|---------------------------------------------------|
| Blue screen after login       | Ensure desktop env + `.xsession` with `startxfce4`|
| Tunnel doesn’t stay up        | Check config, key permissions, server reachability|
| No output in log              | Ensure script is executable, logging is enabled   |
| Port 3390 not listening       | Keep SSH tunnel terminal open                     |

---

**Author**: Deepak Yadav  
**Use Case**: Secure remote RDP access to Ubuntu systems using dynamic reverse SSH tunnels via a proxy server.
