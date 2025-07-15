# 🛠️ AMR Dashboard Startup Script Guide

This document explains the behavior and structure of the `start_dashboard.sh` script used to launch the AMR Dashboard environment, which includes a Node.js backend, Angular frontend, and a MongoDB instance.

---

## 📂 Directory Structure

```
~/AMR_DASHBOARD/
├── AMR-backend/
├── AMR-frontend/
├── Database/
├── logs/
│   ├── YYYY-MM-DD_HH-MM-SS/
│   │   ├── start_dashboard.log
│   │   ├── backend.log
│   │   ├── frontend.log
│   │   └── mongodb.log
│   └── latest -> YYYY-MM-DD_HH-MM-SS/
~/start_dashboard.sh
```

The `start_dashboard.sh` script is located in the **home directory** (`~`). Each time the script runs, a new timestamped folder is created under `logs/`, and a symlink `logs/latest` is updated to point to the newest run.

---

## 🚀 What the Script Does

1. **Sets up logging**:  
   All script output is logged to `start_dashboard.log`.

2. **Checks MongoDB**:
   - If MongoDB is running (port 27017), continues.
   - If not, tries to start it via `systemctl`.
   - If `systemctl` fails, tries `mongod --fork`.

3. **Checks & Restarts Mosquitto(MQTT) server**:
   - Checks if `mosquitto` service is active.
   - If not running, attempts to start it (`sudo systemctl restart mosquitto`).
	   
3. **Kills old frontend processes** (listens on port 4200):
   - Finds and kills any existing process on that port.

4. **Kills existing tmux session** (named `amr_dashboard`):
   - Ensures a fresh environment.

5. **Starts a new tmux session**:
   - Opens two side-by-side panes:
     - Left: backend (`npm run start:dev`)
     - Right: frontend (`ng serve`)

6. **Logs**:
   - Backend logs → `backend.log`
   - Frontend logs → `frontend.log`
   - MongoDB (if manually started) → `mongodb.log`

7. **Symlink**:
   - Updates `logs/latest` to always point to the newest log folder.

---

## 💡 Tips

- Use `tmux attach -t amr_dashboard` to reconnect to the session later.
- Check `logs/latest/start_dashboard.log` for startup diagnostics.
- Watch logs live using `tail -f logs/latest/*.log`.

---

## 🧩 Requirements

- `tmux`
- `node`, `npm`
- `mosquitto`
- `Angular CLI (ng)`
- `mongodb`
- `lsof`, `netcat (nc)`

Make sure these are installed and available in your `$PATH`.

---

Generated on: 2025-06-23 10:41:45
