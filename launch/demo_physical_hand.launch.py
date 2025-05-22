import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import IncludeLaunchDescription
from launch.actions import SetEnvironmentVariable
from launch.launch_description_sources import FrontendLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch.actions import DeclareLaunchArgument

def generate_launch_description():
    """
    Launch camera-based hand tracking with virtual and real hand control.

    Pipeline:
    camera → hand landmark estimation → hand landmark/gesture interpreters → urdf visualization + real hand control

    Topic flow:
    - Camera: publishes /image_raw
    - Hand landmark estimation: subscribes to /image_raw
      publishes /hand_landmark_estimation/bounding_box, /hand_landmark_estimation/hand_landmarks
    - Visualization: subscribes to landmarks/bbox and publishes visualization markers
    - Hand landmark interpreter: subscribes to /hand_landmark_estimation/hand_landmarks
      publishes /joint_states
    - Hand gesture interpreter: subscribes to /hand_landmark_estimation/hand_landmarks
      publishes /joint_states (alternative control method)
    - URDF publishers: subscribe to /joint_states for hand visualization
    - Physical hand controller: subscribes to /joint_states to control the real DexHand
    """
    # Create LaunchConfiguration objects for customizable parameters
    video_device = LaunchConfiguration('video_device', default='/dev/video0')
    landmark_model_type = LaunchConfiguration('landmark_model_type', default='mediapipe_hand_landmark')
    serial_port = LaunchConfiguration('serial_port', default='/dev/ttyUSB0')

    # Define parameter declarations
    video_device_arg = DeclareLaunchArgument(
        'video_device',
        default_value='/dev/video0',
        description='Video device path for camera input'
    )

    landmark_model_type_arg = DeclareLaunchArgument(
        'landmark_model_type',
        default_value='mediapipe_hand_landmark',
        description='Type of hand landmark model to use'
    )

    serial_port_arg = DeclareLaunchArgument(
        'serial_port',
        default_value='/dev/ttyUSB0',
        description='Serial port for the physical DexHand'
    )

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
            'video_device': video_device,
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
            'confidence_threshold': 0.8,
            'landmark_model_type': landmark_model_type,
            'smoothing_enabled': True,
            'smoothing_factor': 0.6,
            'bbox_expansion_scale': 1.5,  # W/A since the hand detection model is not perfect
            'bbox_size_threshold': 32,
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

    # 4. Interpreter for controlling hands
    # 4.1 Hand landmark interpreter for controlling virtual hands
    # SUBSCRIBES: /hand_landmark_estimation/hand_landmarks
    # PUBLISHES: /joint_states
    hand_config_path = os.path.join(arm_control_pkg_dir, 'config/hand/inspire_rh56.yaml')
    hand_landmark_interpreter_node = Node(
        package='arm_hand_control',
        executable='hand_landmark_interpreter',
        name='hand_landmark_interpreter',
        output='screen',
        parameters=[
            {'config_file': hand_config_path},
            {'curl_smooth_factor': 0.8}
        ],
        remappings=[
            ('/hand_landmarks', '/hand_landmark_estimation/hand_landmarks')
        ]
    )

    # 4.2 Hand gesture interpreter (alternative control method)
    # SUBSCRIBES: /hand_landmark_estimation/hand_landmarks
    # PUBLISHES: /joint_states
    hand_gesture_interpreter_node = Node(
        package='arm_hand_control',
        executable='hand_gesture_interpreter',
        name='hand_gesture_interpreter',
        output='screen',
        parameters=[{
            'config_file': hand_config_path,
            'auto_demo_enabled': True,
            'gesture_duration': 1.0,
            'transition_duration': 0.5
        }],
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

    # 6. Real hand control - Inspire RH56 DexHand
    # SUBSCRIBES: /joint_states (implicitly through the node)
    # CONTROLS: Physical Inspire RH56 hand connected via serial
    default_config_file = os.path.join(arm_control_pkg_dir, 'config/hand/inspire_rh56.yaml')
    inspire_rh56_node = Node(
        package='arm_hand_control',
        executable='inspire_rh56_dexhand',
        name='inspire_rh56_dexhand_node',
        parameters=[{
            'config_file': default_config_file,
            'serial_port': serial_port,
            'command_threshold': 5
        }],
        output='screen'
    )

    # 7. Foxglove bridge for visualization in Foxglove Studio
    # BRIDGES: All relevant topics for visualization in Foxglove Studio
    foxglove_bridge_launch = IncludeLaunchDescription(
        FrontendLaunchDescriptionSource(
            os.path.join(get_package_share_directory('foxglove_bridge'), 'launch', 'foxglove_bridge_launch.xml')
        )
    )

    # Return all nodes in execution order with proper grouping
    return LaunchDescription([
        # 1. Launch Arguments - Parameter configuration
        video_device_arg,                     # Camera device configuration
        landmark_model_type_arg,              # Hand landmark model selection
        serial_port_arg,                      # DexHand connection port

        # 2. Environment configuration
        set_tvm_threads,                      # Set TVM_NUM_THREADS environment variable

        # 3. Pipeline nodes - in processing order
        camera_node,                          # Image source
        hand_landmark_estimation_node,        # Hand detection and landmark

        # 4. Visualization nodes
        foxglove_hand_bbox_publisher_node,    # Bounding box visualization
        foxglove_hand_landmark_publisher_node, # Hand landmarks visualization

        # 5. Control nodes
        hand_landmark_interpreter_node,       # Hand control via landmarks
        hand_gesture_interpreter_node,        # Hand control via gestures

        # 6. Robot state publisher nodes
        right_hand_publisher,                 # Virtual right hand visualization
        left_hand_publisher,                  # Virtual left hand visualization

        # 7. Hardware control
        inspire_rh56_node,                    # Real hand control

        # 8. Visualization tools
        foxglove_bridge_launch,               # Visualization bridge
    ])
