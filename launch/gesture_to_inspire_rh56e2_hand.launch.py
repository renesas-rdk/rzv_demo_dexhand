# *********************************************************************************************************************
# Copyright [2025] Renesas Electronics Corporation and/or its licensors. All Rights Reserved.
#
# The contents of this file (the "contents") are proprietary and confidential to Renesas Electronics Corporation
# and/or its licensors ("Renesas") and subject to statutory and contractual protections.
#
# Unless otherwise expressly agreed in writing between Renesas and you: 1) you may not use, copy, modify, distribute,
# display, or perform the contents; 2) you may not use any name or mark of Renesas for advertising or publicity
# purposes or in connection with your use of the contents; 3) RENESAS MAKES NO WARRANTY OR REPRESENTATIONS ABOUT THE
# SUITABILITY OF THE CONTENTS FOR ANY PURPOSE; THE CONTENTS ARE PROVIDED "AS IS" WITHOUT ANY EXPRESS OR IMPLIED
# WARRANTY, INCLUDING THE IMPLIED WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, AND
# NON-INFRINGEMENT; AND 4) RENESAS SHALL NOT BE LIABLE FOR ANY DIRECT, INDIRECT, SPECIAL, OR CONSEQUENTIAL DAMAGES,
# INCLUDING DAMAGES RESULTING FROM LOSS OF USE, DATA, OR PROJECTS, WHETHER IN AN ACTION OF CONTRACT OR TORT, ARISING
# OUT OF OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THE CONTENTS. Third-party contents included in this file may
# be subject to different terms.
# *********************************************************************************************************************

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch.actions import (
    DeclareLaunchArgument,
    OpaqueFunction,
    IncludeLaunchDescription,
)


def launch_setup(context, *args, **kwargs):
    """
    Launch hand gesture interpreter with ros2_control pipeline.

    PIPELINE:
    gesture command → hand interpreter → ros2_control → real hand control

    TOPIC FLOW:
    - External source publishes: /hand_gesture
    - Hand interpreter subscribes to: /hand_gesture and publishes: /inspire_rh56e2_hand_joint_position_controller/commands
    - ros2_control → /inspire_rh56e2_hand_joint_position_controller/commands
    - Real hand controller uses joint states to control physical hand
    """
    # Create LaunchConfiguration objects for customizable parameters
    use_mock_hardware_value = LaunchConfiguration("use_mock_hardware").perform(context)
    hand_side_value = LaunchConfiguration("hand_side").perform(context)
    serial_port_value = LaunchConfiguration("serial_port")

    # Define package directories
    rzv_demo_dexhand_dir = get_package_share_directory("rzv_demo_dexhand")
    hand_config_path = os.path.join(rzv_demo_dexhand_dir, "config/hand/inspire_rh56e2.yaml")

    # Accumulate all nodes/nodes to return
    nodes = []

    # 1. Robot bringup launch file
    inspire_rh56e2_hand_bringup_pkg = get_package_share_directory(
        "inspire_rh56e2_hand_bringup"
    )
    inspire_rh56e2_hand_bringup_launch_file = (
        "inspire_rh56e2_hand_joint_position_control.launch.py"
    )

    robot_bringup_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                inspire_rh56e2_hand_bringup_pkg,
                "launch",
                inspire_rh56e2_hand_bringup_launch_file,
            )
        ),
        launch_arguments={
            "hand_side": hand_side_value,
            "use_mock_hardware": use_mock_hardware_value,
            "serial_port": serial_port_value,
        }.items(),
    )
    nodes.append(robot_bringup_launch)

    # 2. Hand gesture interpreter
    # SUBSCRIBES: /hand_gesture
    # PUBLISHES: /position_controller_command
    hand_gesture_interpreter_node = Node(
        package="arm_hand_control",
        executable="hand_gesture_interpreter",
        name="hand_gesture_interpreter",
        output="screen",
        parameters=[
            {
                "config_file": hand_config_path,
                "auto_demo_enabled": False,
                "gesture_duration": 2.0,
                "transition_duration": 0.5,
            }
        ],
        remappings=[
            (
                "/position_controller_command",
                "/inspire_rh56e2_hand_joint_position_controller/commands",
            ),
        ],
    )
    nodes.append(hand_gesture_interpreter_node)

    return nodes


def generate_launch_description():
    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "serial_port",
                default_value="/dev/ttyUSB0",
                description="Serial port for the physical DexHand",
            ),
            DeclareLaunchArgument(
                "use_mock_hardware",
                default_value="true",
                description="Use mock hardware in ros2_control (recommended for virtual demo)",
            ),
            DeclareLaunchArgument(
                "hand_side",
                default_value="left",
                description="Which hand to control: left or right",
            ),
            OpaqueFunction(function=launch_setup),
        ]
    )
