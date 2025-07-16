# Terminal setup for developmental use

## Files
```
├── robot_bringup.service
└── robot_bringup.sh
```

## Setup in AMR

1. Create a service file named [robot_bringup.service](robot_bringup.service)
```bash
sudo cp robot_bringup.service /etc/systemd/system/robot_bringup.service
cp robot_bringup.sh /home/titan/robot_bringup.sh
```
2. Reload systemd: Run the following command to reload the systemd manager configuration:
```
sudo systemctl daemon-reload
```
3. Enable the service: Enable the service to start on boot:
```
sudo systemctl enable robot_bringup.service
```
4. Start the service: To start the service:
```
sudo systemctl start robot_bringup.service
```
5. Check the service status: Verify that the service is running correctly:
```
sudo systemctl status robot_bringup.service
```

To check logs:
```bash
journalctl -u robot_bringup.service #view
journalctl -u robot_bringup.service -f #view in real time
journalctl SYSLOG_IDENTIFIER=robot_bringup #filter using syslog identifier
```

Working with tmux terminals: Refer to [tmux.md](tmux.md)
## Note

It is assumed that the following condition is met
- /home/titan/.bashrc has the following files lines:
```bash
source /opt/ros/humble/setup.bash
source /home/titan/titan_ws/devel/setup.bash --extend
```


