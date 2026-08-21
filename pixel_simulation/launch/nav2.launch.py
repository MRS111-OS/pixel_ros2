#!/usr/bin/env python3

import copy
import os
import tempfile

import yaml

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.actions import IncludeLaunchDescription
from launch.substitutions import LaunchConfiguration


SENSOR_CONFIGS = {
    "lidar_only": "sensors_lidar_only.yaml",
    "lidar_depth": "sensors_lidar_depth.yaml",
    "lidar_camera": "sensors_lidar_depth.yaml",
}


def merge_parameters(base, override):
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            merge_parameters(base[key], value)
        else:
            base[key] = copy.deepcopy(value)
    return base


def load_parameters(path):
    with open(path, encoding="utf-8") as parameter_file:
        return yaml.safe_load(parameter_file) or {}


def launch_nav2(context):
    sensor_config = LaunchConfiguration("sensor_config").perform(context)
    sensor_file = SENSOR_CONFIGS.get(sensor_config)
    if sensor_file is None:
        supported = ", ".join(SENSOR_CONFIGS)
        raise RuntimeError(
            f"Unsupported sensor_config '{sensor_config}'. Use one of: {supported}."
        )

    simulation_share = get_package_share_directory("pixel_simulation")
    parameter_dir = os.path.join(simulation_share, "config", "nav2_params")
    parameters = load_parameters(os.path.join(parameter_dir, "nav2_base.yaml"))
    merge_parameters(parameters, load_parameters(os.path.join(parameter_dir, "costmap_common.yaml")))
    merge_parameters(parameters, load_parameters(os.path.join(parameter_dir, sensor_file)))

    with tempfile.NamedTemporaryFile(
        mode="w", prefix="pixel_nav2_", suffix=".yaml", delete=False, encoding="utf-8"
    ) as merged_file:
        yaml.safe_dump(parameters, merged_file, sort_keys=False)
        merged_parameters = merged_file.name

    nav2_bringup_share = get_package_share_directory("nav2_bringup")
    return [
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(nav2_bringup_share, "launch", "bringup_launch.py")
            ),
            launch_arguments={
                "namespace": LaunchConfiguration("namespace").perform(context),
                "use_namespace": LaunchConfiguration("use_namespace").perform(context),
                "map": LaunchConfiguration("map").perform(context),
                "use_sim_time": LaunchConfiguration("use_sim_time").perform(context),
                "autostart": LaunchConfiguration("autostart").perform(context),
                "use_composition": LaunchConfiguration("use_composition").perform(context),
                "use_respawn": LaunchConfiguration("use_respawn").perform(context),
                "log_level": LaunchConfiguration("log_level").perform(context),
                "params_file": merged_parameters,
            }.items(),
        )
    ]


def generate_launch_description():
    simulation_share = get_package_share_directory("pixel_simulation")
    default_map = os.path.join(simulation_share, "maps", "warehouse_map.yaml")

    return LaunchDescription(
        [
            DeclareLaunchArgument("sensor_config", default_value="lidar_only"),
            DeclareLaunchArgument("map", default_value=default_map),
            DeclareLaunchArgument("use_sim_time", default_value="true"),
            DeclareLaunchArgument("namespace", default_value=""),
            DeclareLaunchArgument("use_namespace", default_value="false"),
            DeclareLaunchArgument("autostart", default_value="true"),
            DeclareLaunchArgument("use_composition", default_value="True"),
            DeclareLaunchArgument("use_respawn", default_value="False"),
            DeclareLaunchArgument("log_level", default_value="info"),
            OpaqueFunction(function=launch_nav2),
        ]
    )