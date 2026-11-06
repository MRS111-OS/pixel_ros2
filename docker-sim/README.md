# Pixel headless simulation + VDA5050 bridge

Runs the Pixel (Titan) Gazebo simulation headless, plus the VDA5050 MQTT
bridge, in one container -- so the Fleet Manager dashboard can be exercised
against a live simulated robot without physical hardware. Built and
verified against the Momentum Fleet Manager stack (`mrs-webdashboard2.0`).

## What's in here

| File | Purpose |
|---|---|
| `Dockerfile` | `ros:humble-ros-base` + Gazebo/Nav2 + the colcon build, scoped to just `pixel_simulation`/`mqtt_agent_ros2`/`titan_description` (not the whole repo -- see below) |
| `entrypoint.sh` | Launches Gazebo headless, spawns the robot, starts the VDA5050 bridge; templates the YAML config from env vars at container start |
| `vda5050_config.yaml.tmpl`, `vda5050_adapter_params.yaml.tmpl` | `envsubst` templates -- ROS2 Humble's param parser has no env-var support, so these are rendered to real YAML on every container start, not baked into the image |
| `docker-compose.pixel-sim.yml` | The deployable service: joins the Fleet Manager's docker network directly (`mrs-fms_internal`), no published ports |
| `.env.example` | Copy to `.env`, fill in `MQTT_PASSWORD` (the broker's `robots` credential) -- `.env` itself is gitignored |

## Deploy

```bash
cp .env.example .env   # fill in MQTT_PASSWORD
docker compose -f docker-compose.pixel-sim.yml up -d --build
```

Must run on the same host as the Fleet Manager's `mrs-fms_internal` docker
network (or adjust `MQTT_HOST`/`MQTT_PORT`/networks for a remote broker --
see "Topology" below).

Register the simulated robot with the dashboard once it's up:

```bash
curl -X POST http://<fms-backend>:8000/robots -H 'Content-Type: application/json' -d '{
  "robot_id": "pixel_sim_01", "robot_name": "Pixel Sim 01", "type": "AMR",
  "status": "Idle", "battery": 100, "last_updated": "<ISO-8601 now>",
  "enabled": true, "serial_number": "pixel_sim_01", "manufacturer": "Momentum",
  "vehicle_type": "Titan"
}'
```

`robot_id` must equal `ROBOT_SERIAL` in the compose file -- the dashboard
backend extracts the robot id directly from the MQTT topic's serial-number
segment (`uagv/v2/{manufacturer}/{serialNumber}/...`), not from a separate
lookup.

## Why headless, and why not just the upstream launch files

- `pixel_simulation`'s `bringup_sim.launch.py` hardcodes `gz_args: [world, "
  -r"]` with no way to pass `-s` (server-only) through its declared launch
  arguments. The entrypoint calls `ros2 launch ros_gz_sim gz_sim.launch.py`
  directly instead, with `-s -r`, replicating the resource-path env vars
  the upstream launch file sets.
- `pixel_simulation`'s `robot_state_publisher.launch.py` unconditionally
  starts `rviz2`, which needs a display this container doesn't have.
  Rather than add Xvfb overhead for a GUI nobody views, the entrypoint
  launches `robot_state_publisher`, `ros_gz_sim create`, and
  `ros_gz_bridge parameter_bridge` directly -- the same three nodes that
  file's `LaunchDescription` returns, minus `rviz_node`.
- `ros2 run ros_gz_sim create` is a one-shot spawner: it exits 0 once the
  entity exists, which is success, not a crash. It's `wait`ed on directly,
  not added to the long-running-process monitoring pool (which treats any
  exit as fatal and restarts the container) -- see the comment in
  `entrypoint.sh` if this surfaces again elsewhere.

## Build scoping and the build-context split

`pixel_ros2` carries packages this sim+bridge never launches (lidar
drivers, real cameras, AprilTag, coverage planning...), some with rosdep
keys unavailable on this apt mirror. The Dockerfile's `colcon build
--packages-up-to pixel_simulation mqtt_agent_ros2 titan_description` scopes
to the actual dependency closure instead of chasing missing packages for
things that will never run. `titan_description` is listed explicitly
because `pixel_simulation`'s `package.xml` doesn't declare it as a
dependency even though its own launch file needs it (an upstream gap, not
fixed here, this Dockerfile just works around it).

The build uses a named second context (Compose's `additional_contexts`,
matching the pattern in `MRS111-OS/momentum-build`'s `ros2/Dockerfile`):
this directory (`docker-sim/`) is the default context, the repo root one
level up (`..`) is the `product` context. Editing `entrypoint.sh` or the
templates only invalidates layers in this directory's own context, never
the colcon build layer -- without the split, every entrypoint tweak
re-triggers the full ~45-70 minute build.

## Topology

As configured, this expects the Fleet Manager's MQTT broker and this
container on the *same* docker network (`mrs-fms_internal`), talking to the
broker's internal plain listener (`mosquitto:1883`) with `mqtt_use_tls:
false` in the generated config. For a site with physical robots and a
remote broker, point `MQTT_HOST`/`MQTT_PORT` at the public TLS listener
(`mqtt.fms.momentumrobotics.in:8883`) and set `mqtt_use_tls: true` instead
-- see the `vda5050_connector` submodule's fix notes for why this needs to
be explicit rather than inferred.

## The `ros_amr_interop` submodule fix

`vda5050_connector`'s `mqtt_bridge.py` (upstream, in `ros_amr_interop`)
enabled TLS purely because a username was set, with no way to opt out for
an authenticated-but-plain-TCP broker. Fixed in
`MRS111-OS/ros_amr_interop` (forked from `inorbit-ai/ros_amr_interop`,
this repo's submodule now points there instead of upstream) --
backward-compatible: unset `mqtt_use_tls` still infers TLS from
`mqtt_username`'s presence exactly as before, so the existing physical
fleet's configs (which never set this key) are unaffected. Only a config
that explicitly sets `mqtt_use_tls: false` gets the new behavior. See that
repo's commit for the full writeup and the verification against rclpy's
actual parameter semantics.
