import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import IncludeLaunchDescription
from launch.actions import SetEnvironmentVariable
from launch.launch_description_sources import FrontendLaunchDescriptionSource

def generate_launch_description():
    """
    Launch camera-based hand tracking with virtual hand control.
    Pipeline: camera → hand landmark estimation → hand control → urdf visualization

    Topic flow:
    - Camera publishes: /image_raw
    - Hand landmark estimation subscribes to: /image_raw
      and publishes: /hand_landmark_estimation/bounding_box, /hand_landmark_estimation/hand_landmarks
    - Visualization nodes subscribe to landmarks/bbox and publish visualizations
    - Hand interpreter subscribes to: /hand_landmark_estimation/hand_landmarks
      and publishes: /joint_states
    - URDF publishers use joint states to visualize the hands
    """
    # Define package directories
    arm_control_pkg_dir = get_package_share_directory('arm_hand_control')
    inspire_pkg_dir = get_package_share_directory('inspire_rh56_urdf')
    foxglove_keypoint_pkg_dir = get_package_share_directory('foxglove_keypoint_publisher')

    # Set TVM_NUM_THREADS environment variable for hand landmark estimation
    set_tvm_threads = SetEnvironmentVariable('TVM_NUM_THREADS', '2')

    # 1. Camera node
    # PUBLISHES: /image_raw
    camera_node = Node(
        package='v4l2_camera',
        executable='v4l2_camera_node',
        name='v4l2_camera',
        parameters=[{
            'video_device': '/dev/video0',
            'output_encoding': 'yuv422_yuy2',
            'image_size': [640, 480]
        }]
    )

    # 2. Hand landmark estimation node
    # SUBSCRIBES: /image_raw
    # PUBLISHES: /hand_landmark_estimation/bounding_box, /hand_landmark_estimation/hand_landmarks
    hand_landmark_estimation_node = Node(
        package='rzv_pose_estimation',
        executable='hand_landmark_estimation',
        name='hand_landmark_estimation',
        parameters=[{
            'confidence_threshold': 0.7,
            'landmark_model_type': 'mediapipe_hand_landmark',
            'smoothing_enabled': True,
            'smoothing_factor': 0.6,
            'bbox_expansion_scale': 1.2, # W/A since the hand detection model is not perfect
        }],
        remappings=[
            ('/image_raw', '/image_raw'),
            ('/bounding_box', '/hand_landmark_estimation/bounding_box'),
            ('/hand_landmarks', '/hand_landmark_estimation/hand_landmarks'),
        ],
        output='screen',
        arguments=['--ros-args', '--log-level', 'INFO']
    )

    # 3. Visualization nodes for Foxglove Studio
    # 3.1 Bounding box visualization
    # SUBSCRIBES: /hand_landmark_estimation/bounding_box
    # PUBLISHES: /hand_landmark_estimation/bbox_visualization
    bbox_config_path = os.path.join(foxglove_keypoint_pkg_dir, 'config/poses/bounding_box.yaml')
    foxglove_hand_bbox_publisher_node = Node(
        package='foxglove_keypoint_publisher',
        executable='foxglove_keypoint_publisher_node',
        name='foxglove_hand_bbox_publisher',
        parameters=[{'config_file': bbox_config_path}],
        remappings=[
            ('/keypoint_poses', '/hand_landmark_estimation/bounding_box'),
            ('/keypoint_visualization', '/bbox_visualization')
        ],
        output='screen'
    )

    # 3.2 Hand landmarks visualization
    # SUBSCRIBES: /hand_landmark_estimation/hand_landmarks
    # PUBLISHES: /hand_landmark_estimation/landmarks_visualization
    landmark_config_path = os.path.join(foxglove_keypoint_pkg_dir, 'config/poses/hand_landmarks.yaml')
    foxglove_hand_landmark_publisher_node = Node(
        package='foxglove_keypoint_publisher',
        executable='foxglove_keypoint_publisher_node',
        name='foxglove_hand_landmark_publisher',
        parameters=[{'config_file': landmark_config_path}],
        remappings=[
            ('/keypoint_poses', '/hand_landmark_estimation/hand_landmarks'),
            ('/keypoint_visualization', '/landmarks_visualization')
        ],
        output='screen'
    )

    # 4. Hand landmark interpreter for controlling virtual hands
    # SUBSCRIBES: /hand_landmark_estimation/hand_landmarks
    # PUBLISHES: /joint_states, /joint_states
    hand_config_path = os.path.join(arm_control_pkg_dir, 'config/hand/inspire_rh56.yaml')
    hand_interpreter_node = Node(
        package='arm_hand_control',
        executable='hand_landmark_interpreter',
        name='hand_landmark_interpreter',
        output='screen',
        parameters=[{'config_file': hand_config_path}],
        remappings=[
            ('/hand_landmarks', '/hand_landmark_estimation/hand_landmarks')
        ]
    )

    # 5. URDF state publishers for visualization
    # 5.1 Right hand URDF publisher
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

    # 5.2 Left hand URDF publisher
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

    # 6. Foxglove bridge for visualization in Foxglove Studio
    # BRIDGES: All relevant topics for visualization in Foxglove Studio
    foxglove_bridge_launch = IncludeLaunchDescription(
        FrontendLaunchDescriptionSource(
            os.path.join(get_package_share_directory('foxglove_bridge'), 'launch', 'foxglove_bridge_launch.xml')
        )
    )

    # Return all nodes in execution order
    return LaunchDescription([
        set_tvm_threads,                      # Set environment variable for TVM
        camera_node,                          # Image source
        hand_landmark_estimation_node,        # Hand detection and landmark
        foxglove_hand_bbox_publisher_node,    # Visualizations
        foxglove_hand_landmark_publisher_node,
        hand_interpreter_node,                # Hand control
        right_hand_publisher,                 # Virtual hands
        left_hand_publisher,
        foxglove_bridge_launch,               # Visualization bridge
    ])
