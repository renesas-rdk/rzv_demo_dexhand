# *********************************************************************************************************************
# Copyright [2026] Renesas Electronics Corporation and/or its licensors. All Rights Reserved.
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
from launch.actions import (
    IncludeLaunchDescription,
    SetEnvironmentVariable,
    DeclareLaunchArgument,
    OpaqueFunction,
)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


def launch_setup(context, *args, **kwargs):
    """
    Launch camera-based hand tracking with virtual hand control.

    Pipeline:
    camera → hand landmark estimation → hand landmark/gesture interpreters
      → ros2_control position controller → joint_state_broadcaster → urdf visualization

    Topic flow:
    - Camera: publishes /image_raw
    - Hand landmark estimation: subscribes to /image_raw
      publishes /hand_landmark_estimation/bounding_box, /hand_landmark_estimation/hand_landmarks
    - Visualization: subscribes to landmarks/bbox and publishes visualization markers
    - Hand landmark interpreter: subscribes to /hand_landmark_estimation/hand_landmarks
      publishes /ruiyan_rh2_hand_joint_position_controller/commands
    - Hand gesture interpreter: subscribes to /hand_landmark_estimation/hand_landmarks
      publishes /ruiyan_rh2_hand_joint_position_controller/commands
    - ros2_control position controller: subscribes to /ruiyan_rh2_hand_joint_position_controller/commands
    - joint_state_broadcaster: publishes /joint_states
    - URDF publishers: subscribe to /joint_states for hand visualization (from ros2_control)

    """
    # Create LaunchConfiguration objects for customizable parameters
    use_mock_hardware_value = LaunchConfiguration("use_mock_hardware").perform(context)
    hand_side_value = LaunchConfiguration("hand_side").perform(context)
    can_interface_value = LaunchConfiguration("can_interface").perform(context)
    hand_speed_value = LaunchConfiguration("hand_speed").perform(context)
    landmark_model_type = LaunchConfiguration("landmark_model_type")
    video_device = LaunchConfiguration("video_device")

    # Define package directories
    foxglove_keypoint_pkg_dir = get_package_share_directory(
        "foxglove_keypoint_publisher"
    )
    rzv_demo_dexhand_dir = get_package_share_directory("rzv_demo_dexhand")

    # Shared hand config path used by both interpreter nodes
    hand_config_path = os.path.join(rzv_demo_dexhand_dir, "config/hand/ruiyan_rh2.yaml")

    # Accumulate all nodes/nodes to return
    nodes = []

    # Set TVM_NUM_THREADS environment variable for hand landmark estimation performance
    set_tvm_threads = SetEnvironmentVariable("TVM_NUM_THREADS", "2")
    nodes.append(set_tvm_threads)

    # 1. Robot bringup launch file
    ruiyan_rh2_hand_bringup_pkg = get_package_share_directory("ruiyan_rh2_hand_bringup")
    ruiyan_rh2_hand_bringup_launch_file = (
        "ruiyan_rh2_hand_joint_position_control.launch.py"
    )

    robot_bringup_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                ruiyan_rh2_hand_bringup_pkg,
                "launch",
                ruiyan_rh2_hand_bringup_launch_file,
            )
        ),
        launch_arguments={
            "hand_side": hand_side_value,
            "use_mock_hardware": use_mock_hardware_value,
            "can_interface": can_interface_value,
            "hand_speed": hand_speed_value,
        }.items(),
    )
    nodes.append(robot_bringup_launch)

    # 2. Camera node
    # PUBLISHES: /image_raw
    camera_node = Node(
        package="v4l2_camera",
        executable="v4l2_camera_node",
        name="v4l2_camera",
        parameters=[
            {
                "video_device": video_device,
                "output_encoding": "yuv422_yuy2",
                "image_size": [640, 480],
            }
        ],
    )
    nodes.append(camera_node)

    # 3. Hand landmark estimation node
    # SUBSCRIBES: /image_raw
    # PUBLISHES:  /hand_landmark_estimation/bounding_box
    #             /hand_landmark_estimation/hand_landmarks
    hand_landmark_estimation_node = Node(
        package="rzv_pose_estimation",
        executable="hand_landmark_estimation",
        name="hand_landmark_estimation",
        parameters=[
            {
                "confidence_threshold": 0.8,
                "landmark_model_type": landmark_model_type,
                "smoothing_enabled": True,
                "smoothing_factor": 0.6,
                "bbox_expansion_scale": 1.5,
                "bbox_size_threshold": 32,
            }
        ],
        remappings=[
            ("/bounding_box", "/hand_landmark_estimation/bounding_box"),
            ("/hand_landmarks", "/hand_landmark_estimation/hand_landmarks"),
        ],
        output="screen",
        arguments=["--ros-args", "--log-level", "INFO"],
    )
    nodes.append(hand_landmark_estimation_node)

    # 4. Foxglove Studio visualization nodes

    # 4.1 Bounding box visualization
    # SUBSCRIBES: /hand_landmark_estimation/bounding_box
    # PUBLISHES:  /bbox_visualization
    bbox_config_path = os.path.join(
        foxglove_keypoint_pkg_dir, "config/poses/bounding_box.yaml"
    )
    foxglove_hand_bbox_publisher_node = Node(
        package="foxglove_keypoint_publisher",
        executable="foxglove_keypoint_publisher_node",
        name="foxglove_hand_bbox_publisher",
        parameters=[{"config_file": bbox_config_path}],
        remappings=[
            ("/keypoint_poses", "/hand_landmark_estimation/bounding_box"),
            ("/keypoint_visualization", "/bbox_visualization"),
        ],
        output="screen",
    )
    nodes.append(foxglove_hand_bbox_publisher_node)

    # 4.2 Hand landmarks visualization
    # SUBSCRIBES: /hand_landmark_estimation/hand_landmarks
    # PUBLISHES:  /landmarks_visualization
    landmark_config_path = os.path.join(
        foxglove_keypoint_pkg_dir, "config/poses/hand_landmarks.yaml"
    )
    foxglove_hand_landmark_publisher_node = Node(
        package="foxglove_keypoint_publisher",
        executable="foxglove_keypoint_publisher_node",
        name="foxglove_hand_landmark_publisher",
        parameters=[{"config_file": landmark_config_path}],
        remappings=[
            ("/keypoint_poses", "/hand_landmark_estimation/hand_landmarks"),
            ("/keypoint_visualization", "/landmarks_visualization"),
        ],
        output="screen",
    )
    nodes.append(foxglove_hand_landmark_publisher_node)

    # 5. Interpreter for controlling hands
    # 5.1 Hand gesture interpreter
    # SUBSCRIBES: /hand_landmark_estimation/hand_landmarks
    # PUBLISHES:  /ruiyan_rh2_hand_joint_position_controller/commands
    hand_gesture_interpreter_node = Node(
        package="arm_hand_control",
        executable="hand_gesture_interpreter",
        name="hand_gesture_interpreter",
        output="screen",
        parameters=[
            {
                "config_file": hand_config_path,
                "auto_demo_enabled": True,
                "gesture_duration": 2.0,
                "transition_duration": 1.5,
                "hand_speed": float(hand_speed_value),
            }
        ],
        remappings=[
            ("/hand_landmarks", "/hand_landmark_estimation/hand_landmarks"),
            (
                "/position_controller_command",
                "/ruiyan_rh2_hand_joint_position_controller/commands",
            ),
        ],
    )
    nodes.append(hand_gesture_interpreter_node)

    # 5.2 Hand landmark interpreter
    # SUBSCRIBES: /hand_landmark_estimation/hand_landmarks
    # PUBLISHES:  /ruiyan_rh2_hand_joint_position_controller/commands
    hand_landmark_interpreter_node = Node(
        package="arm_hand_control",
        executable="hand_landmark_interpreter",
        name="hand_landmark_interpreter",
        output="screen",
        parameters=[
            {"config_file": hand_config_path},
            {"curl_smooth_factor": 0.8},
        ],
        remappings=[
            ("/hand_landmarks", "/hand_landmark_estimation/hand_landmarks"),
            (
                "/position_controller_command",
                "/ruiyan_rh2_hand_joint_position_controller/commands",
            ),
        ],
    )
    nodes.append(hand_landmark_interpreter_node)

    return nodes


def generate_launch_description():
    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "use_mock_hardware",
                default_value="false",
                description="Use mock hardware for testing (true/false)",
            ),
            DeclareLaunchArgument(
                "hand_side",
                default_value="left",
                description="Which hand to control: left or right",
            ),
            DeclareLaunchArgument(
                "can_interface",
                default_value="can2",
                description="CAN interface for hand hardware communication (e.g., can0, can1, can2)",
            ),
            DeclareLaunchArgument(
                "hand_speed", default_value="1500", description="Hand motor speed"
            ),
            DeclareLaunchArgument(
                "landmark_model_type",
                default_value="mediapipe_hand_landmark",
                description="Type of hand landmark model to use",
            ),
            DeclareLaunchArgument(
                "video_device",
                default_value="/dev/video0",
                description="Video device path for camera input",
            ),
            OpaqueFunction(function=launch_setup),
        ]
    )
