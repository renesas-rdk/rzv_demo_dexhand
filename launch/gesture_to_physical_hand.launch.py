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
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import FrontendLaunchDescriptionSource

def generate_launch_description():
    """
    Launch hand gesture interpreter with virtual and physical hand control.

    PIPELINE:
    gesture command → hand interpreter → urdf visualization + real hand control

    TOPIC FLOW:
    - External source publishes: /hand_gesture
    - Hand interpreter subscribes to: /hand_gesture and publishes: /joint_states
    - URDF publishers use joint states to visualize both hands
    - Real hand controller uses joint states to control physical hand
    """
    # Define package directories
    inspire_pkg_dir = get_package_share_directory('inspire_rh56_urdf')
    inspire_rh56_config_pkg_dir = get_package_share_directory('inspire_rh56_dexhand')

    # 1. Hand gesture interpreter
    # SUBSCRIBES: /hand_gesture
    # PUBLISHES: /joint_states
    hand_config_path = os.path.join(inspire_rh56_config_pkg_dir, 'config/inspire_rh56.yaml')
    hand_interpreter_node = Node(
        package='arm_hand_control',
        executable='hand_gesture_interpreter',
        name='hand_gesture_interpreter',
        output='screen',
        parameters=[{'config_file': hand_config_path}]
    )

    # 2. URDF state publishers for visualization
    # 2.1 Right hand URDF publisher
    # SUBSCRIBES: /joint_states
    # PUBLISHES: /tf, /tf_static (for right hand visualization)
    right_hand_urdf = os.path.join(inspire_pkg_dir, 'urdf', 'inspire_hand_right.urdf')
    with open(right_hand_urdf, 'r') as file:
        right_hand_description = file.read()

    right_hand_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='right_hand_state_publisher',
        output='screen',
        parameters=[
            {'robot_description': right_hand_description},
            {'frame_prefix': 'right_hand/'}
        ],
        remappings=[
            ('/robot_description', '/right_hand/robot_description')
        ]
    )

    # 2.2 Left hand URDF publisher
    # SUBSCRIBES: /joint_states
    # PUBLISHES: /tf, /tf_static (for left hand visualization)
    left_hand_urdf = os.path.join(inspire_pkg_dir, 'urdf', 'inspire_hand_left.urdf')
    with open(left_hand_urdf, 'r') as file:
        left_hand_description = file.read()

    left_hand_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='left_hand_state_publisher',
        output='screen',
        parameters=[
            {'robot_description': left_hand_description},
            {'frame_prefix': 'left_hand/'}
        ],
        remappings=[
            ('/robot_description', '/left_hand/robot_description')
        ]
    )

    # 3. Create a common camera reference frame for both hands
    # Places hands into a common camera reference frame
    # SUBSCRIBES: /joint_states
    # PUBLISHES: /tf, /tf_static (for camera reference frame)
    world_frame_publisher_right = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='world_frame_publisher_right',
        arguments=['0', '0', '0', '0', '0', '0', '1', 'camera', 'right_hand/base']
    )

    world_frame_publisher_left = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='world_frame_publisher_left',
        arguments=['0', '0', '0', '0', '0', '0', '1', 'camera', 'left_hand/base']
    )

    # 4. Real hand control - Inspire RH56 DexHand
    # SUBSCRIBES: /joint_states (implicitly through the node)
    # CONTROLS: Physical Inspire RH56 hand connected via serial
    default_config_file = os.path.join(inspire_rh56_config_pkg_dir, 'config/inspire_rh56.yaml')
    inspire_rh56_node = Node(
        package='inspire_rh56_dexhand',
        executable='inspire_rh56_dexhand',
        name='inspire_rh56_dexhand_node',
        parameters=[
            {'config_file': default_config_file,
             'serial_port': '/dev/ttyUSB0',
             'command_threshold': 0}
        ],
        output='screen'
    )

    # 5. Foxglove bridge for external visualization
    foxglove_bridge_launch = IncludeLaunchDescription(
        FrontendLaunchDescriptionSource(
            os.path.join(get_package_share_directory('foxglove_bridge'), 'launch', 'foxglove_bridge_launch.xml')
        )
    )

    # Return all nodes in logical execution order
    return LaunchDescription([
        hand_interpreter_node,          # Hand gesture control
        right_hand_publisher,           # Virtual hand state publishers
        left_hand_publisher,
        world_frame_publisher_right,    # World reference frames
        world_frame_publisher_left,
        inspire_rh56_node,              # Real hand control
        foxglove_bridge_launch,         # Visualization bridge
    ])
