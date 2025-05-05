import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import FrontendLaunchDescriptionSource

def generate_launch_description():
    """
    Launch hand gesture interpreter with virtual hand control.

    PIPELINE:
    gesture command → hand interpreter → urdf visualization

    TOPIC FLOW:
    - External source publishes: /hand_gesture
    - Hand interpreter subscribes to: /hand_gesture and publishes: /joint_states
    - URDF publishers use joint states to visualize both hands
    """
    # Define package directories
    arm_control_pkg_dir = get_package_share_directory('arm_hand_control')
    inspire_pkg_dir = get_package_share_directory('inspire_rh56_urdf')

    # 1. Hand gesture interpreter
    # SUBSCRIBES: /hand_gesture
    # PUBLISHES: /joint_states
    hand_config_path = os.path.join(arm_control_pkg_dir, 'config/hand/inspire_rh56.yaml')
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

    # 4. Foxglove bridge for external visualization
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
        foxglove_bridge_launch,         # Visualization bridge
    ])
