#!/usr/bin/env python3
"""Compose Titan Nav2 overlays and delegate startup to upstream Nav2 bringup."""

import copy
import os
import tempfile

import yaml

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, OpaqueFunction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


VALID_VARIANTS = ("lidar_only", "lidar_camera", "lidar_depth")
VALID_MODES = ("sim", "real")


def deep_merge(base, override):
    """Recursively merge mappings; null removes a prior mapping entry."""
    for key, value in override.items():
        if value is None:
            base.pop(key, None)
            continue
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            deep_merge(base[key], value)
        else:
            base[key] = copy.deepcopy(value)
    return base


def load_yaml(path):
    with open(path, encoding="utf-8") as yaml_file:
        data = yaml.safe_load(yaml_file) or {}
    if not isinstance(data, dict):
        raise RuntimeError(f"Nav2 parameter file must contain a YAML mapping: {path}")
    return data


def resolve_use_sim_time(mode, requested):
    if not requested:
        return "true" if mode == "sim" else "false"
    if requested.lower() not in ("true", "false"):
        raise RuntimeError("use_sim_time must be 'true' or 'false'.")
    return requested.lower()


def launch_navigation(context):
    variant = LaunchConfiguration("variant").perform(context)
    mode = LaunchConfiguration("mode").perform(context)
    if variant not in VALID_VARIANTS:
        raise RuntimeError(
            f"Invalid robot variant: {variant}. Expected: {', '.join(VALID_VARIANTS)}."
        )
    if mode not in VALID_MODES:
        raise RuntimeError(f"Invalid mode: {mode}. Expected: {', '.join(VALID_MODES)}.")

    use_sim_time = resolve_use_sim_time(
        mode, LaunchConfiguration("use_sim_time").perform(context)
    )
    titan_nav_share = get_package_share_directory("titan_nav")
    nav2_bringup_share = get_package_share_directory("nav2_bringup")
    config_dir = os.path.join(titan_nav_share, "config")
    baseline = LaunchConfiguration("params_file").perform(context)

    merged = load_yaml(baseline)
    for overlay in (
        os.path.join(config_dir, "common", "nav2_common.yaml"),
        os.path.join(config_dir, "variants", f"{variant}.yaml"),
        os.path.join(config_dir, "modes", f"{mode}.yaml"),
    ):
        deep_merge(merged, load_yaml(overlay))

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", prefix="titan_nav2_", delete=False, encoding="utf-8"
    ) as merged_file:
        yaml.safe_dump(merged, merged_file, sort_keys=False)
        merged_params_file = merged_file.name

    return [
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(nav2_bringup_share, "launch", "bringup_launch.py")
            ),
            launch_arguments={
                "namespace": LaunchConfiguration("namespace").perform(context),
                "use_namespace": LaunchConfiguration("use_namespace").perform(context),
                "slam": LaunchConfiguration("slam").perform(context),
                "map": LaunchConfiguration("map").perform(context),
                "use_sim_time": use_sim_time,
                "params_file": merged_params_file,
                "autostart": LaunchConfiguration("autostart").perform(context),
                "use_composition": LaunchConfiguration("use_composition").perform(context),
                "use_respawn": LaunchConfiguration("use_respawn").perform(context),
                "log_level": LaunchConfiguration("log_level").perform(context),
            }.items(),
        )
    ]


def generate_launch_description():
    titan_nav_share = get_package_share_directory("titan_nav")
    nav2_bringup_share = get_package_share_directory("nav2_bringup")

    return LaunchDescription(
        [
            DeclareLaunchArgument("variant", default_value="lidar_only"),
            DeclareLaunchArgument("mode", default_value="real"),
            DeclareLaunchArgument("slam", default_value="False"),
            DeclareLaunchArgument(
                "map",
                default_value=os.path.join(titan_nav_share, "maps", "momentum_map.yaml"),
                description="Full path to the map YAML file.",
            ),
            DeclareLaunchArgument(
                "params_file",
                default_value=os.path.join(nav2_bringup_share, "params", "nav2_params.yaml"),
                description="Baseline Nav2 parameter YAML before Titan overlays.",
            ),
            DeclareLaunchArgument(
                "use_sim_time",
                default_value="",
                description="Optional override; empty derives from mode (sim=true, real=false).",
            ),
            DeclareLaunchArgument("namespace", default_value=""),
            DeclareLaunchArgument("use_namespace", default_value="false"),
            DeclareLaunchArgument("autostart", default_value="true"),
            DeclareLaunchArgument("use_composition", default_value="True"),
            DeclareLaunchArgument("use_respawn", default_value="False"),
            DeclareLaunchArgument("log_level", default_value="info"),
            OpaqueFunction(function=launch_navigation),
        ]
    )
