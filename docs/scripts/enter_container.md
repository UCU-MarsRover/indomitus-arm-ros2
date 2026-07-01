# Container Entry Script (`enter_container.sh`)

The `enter_container.sh` script provides an interface to ensure the required Docker container is running and opens an interactive shell. It supports both local development and remote execution on the Jetson.

## Running the Script

You can run this script from any folder; it will locate the repository root automatically. The script requires a subcommand to specify your target environment: `local` or `jetson`.

It will automatically start or create the container if necessary, and then open an interactive shell. If using the `jetson` command, it will also automatically attempt to connect to the Jetson's Wi-Fi hotspot and establish an SSH connection.

Enter the local development container:
```bash
./scripts/enter_container.sh local
```

Enter the remote production container on the Jetson:
```bash
./scripts/enter_container.sh jetson
```

## Configuration Flags & Defaults

The script accepts the following flags to override defaults depending on the subcommand used.

| Flag | Applies To | Description | Default |
|---|---|---|---|
| `-n`, `--name` | local, jetson | Docker container name | `arm_dev` (local), `arm_prod` (jetson) |
| `-c`, `--compose` | local, jetson | Path to Compose file | `docker-compose.yaml` (local), `docker-compose.prod.yaml` (jetson) |
| `-r`, `--ros-distro` | local | ROS 2 distribution name | `humble` |
| `-w`, `--workspace` | local | ROS 2 workspace path inside container | `/opt/ws` |
| `-u`, `--user` | jetson | Jetson SSH username | `indomitus-arm` |
| `-i`, `--ip` | jetson | Jetson IP address | `10.42.0.1` |
| `-d`, `--dir` | jetson | Remote deployment directory | `/home/indomitus-arm/indomitus-arm-ros2/` |
| `-w`, `--ssid` | jetson | Wi-Fi SSID of the Jetson hotspot | `IndomitusRover` |
| `-p`, `--pass` | jetson | Wi-Fi password for the hotspot | `12345678` |
| `-h`, `--help` | local, jetson | Display the help message and exit | N/A |