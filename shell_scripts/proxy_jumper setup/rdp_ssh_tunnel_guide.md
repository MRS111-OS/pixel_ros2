# Remote RDP Access via SSH Tunnel with Proxy Jumper

This document outlines the complete working setup to access a remote Ubuntu machine's desktop (via `xrdp`) through an SSH tunnel using a **jump server**. It supports both same-network and remote access cases.

---

## ✅ Part A: Configure the Host (RDP Server) – Ubuntu Machine

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

### 4. Check if RDP is listening

```bash
sudo ss -tuln | grep 3389
```

Expected output:

```
LISTEN 0 128 *:3389 *:*
```

---

## ✅ Part B: Local LAN Access (Optional)

If both client and server are in the same network:

- Use any RDP client (e.g., Microsoft Remote Desktop)
- Connect to:
  ```
  <remote_machine_ip>:3389
  ```
- Login with Ubuntu username and password.

---

## ✅ Part C: Remote Access via Proxy Jumper

### 🧠 Architecture

```
[Client Mac] --SSH--> [Proxy Server] --SSH--> [Remote Ubuntu with xrdp]
```

---

### 1. Set up persistent reverse tunnel on the Host (optional)

Create a systemd service `/etc/systemd/system/ssh-tunnel@.service` on the remote Ubuntu machine:

```ini
[Unit]
Description=Reverse SSH Tunnel for %i
After=network.target

[Service]
User=%i
ExecStart=/usr/bin/ssh -o "ServerAliveInterval=60" -o "ServerAliveCountMax=3" -o "StrictHostKeyChecking=accept-new" \
  -i /home/%i/.ssh/proxyjumper_tahjzf6z \
  -N -R /PC31:localhost:22 tahjzf6z2@api2.proxypilot.org
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable it:

```bash
sudo systemctl daemon-reload
sudo systemctl enable ssh-tunnel@user
sudo systemctl start ssh-tunnel@user
```

---

### 2. At Client Side (Mac), create SSH tunnel using proxy

```bash
ssh -v -o ProxyCommand="ssh -i ~/.ssh/proxyjumper_tahjzf6z tahjzf6z2@api2.proxypilot.org -W/PC31" \
    -L 3390:localhost:3389 user@user-NUC12WSH-B
```

This forwards:

```
localhost:3390 (your Mac) → remote:3389 (xrdp port)
```

Keep this terminal open while connecting via RDP.

---

### 3. Verify local port is listening (on your Mac)

```bash
lsof -i :3390
```

Expected output shows `ssh` listening on `localhost:3390`.

---

### 4. Connect using RDP client

Use **Microsoft Remote Desktop** on your Mac:

- **PC name**: `127.0.0.1:3390`
- **Username**: Ubuntu machine username
- **Password**: Ubuntu login password
- **Session**: XFCE or default desktop (configured via `.xsession`)

> If needed:
>
> ```bash
> echo "startxfce4" > ~/.xsession
> ```

---

## ✅ Common Troubleshooting

| Problem                 | Solution                                      |
| ----------------------- | --------------------------------------------- |
| Blue screen after login | Ensure desktop environment + `.xsession` file |
| Port 3390 not listening | Check SSH tunnel syntax, keep terminal open   |
| RDP login fails         | Verify correct user/pass on remote machine    |
| Jump server fails       | Check key permissions and host reachability   |

---

## 🧪 Summary of Important Commands

| Task                       | Command                                     |             |
| -------------------------- | ------------------------------------------- | ----------- |
| Install xrdp               | `sudo apt install xrdp`                     |             |
| Start xrdp                 | `sudo systemctl start xrdp`                 |             |
| Check RDP port on server   | \`sudo ss -tuln                             | grep 3389\` |
| Check tunnel port on Mac   | `lsof -i :3390`                             |             |
| SSH tunnel via jump server | See long `ssh -v -o ProxyCommand=...` above |             |
| Connect via RDP (on Mac)   | `127.0.0.1:3390` in Microsoft RDP           |             |

---

**Author**: Deepak Yadav\
**Use Case**: Accessing Ubuntu desktops from a remote location securely via proxy + RDP tunneling.

