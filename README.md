# RZ/V Demo DexHand

This package provides launch files and configurations for demonstrating dexterous hand control on Renesas RZ/V platforms. It integrates vision-based pose estimation with both virtual and physical hand control.

## Overview

The RZ/V Demo DexHand package enables:
- Hand landmark estimation and interpretation
- Simultaneous control of virtual and physical dexterous hands
- Visualization through Foxglove Studio

## Dependencies

### Vision and Perception
- `rzv_pose_estimation`: Provides pose estimation capabilities on Renesas RZ/V platforms
- `v4l2_camera`: Camera interface for video capture
- `foxglove_keypoint_publisher`: Publishes keypoints for visualization

### Hand Control and Visualization
- `arm_hand_control`: Core control logic for the dexterous hand
- `inspire_rh56_urdf`: URDF models for the Inspire RH56 dexterous hand
- `robot_state_publisher`: Publishes TF information based on joint states
- `tf2_ros`: Transform library for coordinate frames

### Visualization Bridge
- `foxglove_bridge`: Bridges ROS 2 to Foxglove Studio for visualization

## Installation and Setup

### ROS2 Jazzy Installation

Before installing the package dependencies, ensure you have ROS 2 Jazzy installed on your Ubuntu system:

```bash
# Install ROS2 Jazzy base
sudo apt update
sudo apt install ros-jazzy-ros-base

# Source ROS2 in the current shell
source /opt/ros/jazzy/setup.bash
```

For detailed installation instructions, follow the [official ROS2 Jazzy installation guide](https://docs.ros.org/en/jazzy/Installation/Ubuntu-Install-Debs.html).

### Demo Packages Installation

Before running the demos, ensure all required dependencies are installed:

```bash
# Clone and build all required packages in your workspace
cd <your_ros2_ws>/src
git clone <repository_url_for_arm_hand_control>
git clone <repository_url_for_foxglove_keypoint_publisher>
git clone <repository_url_for_inspire_rh56_urdf>
git clone <repository_url_for_rzv_demo_dexhand>
git clone <repository_url_for_rzv_model>
git clone <repository_url_for_rzv_pose_estimation>

# Build the workspace
cd <your_ros2_ws>
colcon build --cmake-args -DCMAKE_BUILD_TYPE=Release
```

### RZV ROS2 Package Dependencies Installation

Install the TVM TOOLCHAIN runtime library:

```bash
# Location in the RZV TVM: /drp-ai_tvm/obj/build_runtime/V2H/libtvm_runtime.so
sudo cp libtvm_runtime.so /usr/lib/aarch64-linux-gnu/renesas
```

Use rosdep to install the remaining dependencies:

```bash
# Initialize and update rosdep
sudo rosdep init
rosdep update

# Install dependencies using rosdep
rosdep install \
    --from-paths install/arm_hand_control \
                 install/foxglove_keypoint_publisher \
                 install/inspire_rh56_urdf \
                 install/rzv_demo_dexhand \
                 install/rzv_pose_estimation \
    --ignore-src -r -y
```

### Serial Port Setup

To access the physical DexHand through the serial port, the user needs permission to access `/dev/ttyUSB0`:

```bash
# Add your user to the dialout group to enable access to /dev/ttyUSB0
sudo usermod -a -G dialout $USER
```

NOTE: You must log out and log back in to your user session for this change to take effect.

### Setup Environment

After building your workspace, you must source the setup script to make the packages visible to ROS:

```bash
source <your_ros2_ws>/install/setup.bash
```

It's recommended to add this line to your `~/.bashrc` file for automatic sourcing in new terminal sessions.

## Launch Files

### demo_virtual_hands.launch.py

This launch file sets up a camera-based hand tracking system that controls virtual hands:

```
PIPELINE:
camera → hand landmark estimation → hand landmark/gesture interpreters → urdf visualization

TOPIC FLOW:
- Camera publishes: /image_raw
- Hand landmark estimation subscribes to: /image_raw and publishes: /hand_landmark_estimation/bounding_box, /hand_landmark_estimation/hand_landmarks
- Visualization nodes subscribe to landmarks/bbox and publish visualizations
- Hand interpreters subscribe to: /hand_landmark_estimation/hand_landmarks and publish: /joint_states
- URDF publishers use joint states to visualize the hands
```

Components included in this launch file:
1. **Camera Node**: Captures video input for hand tracking
2. **Hand Landmark Estimation**: Detects hands and extracts landmark points
3. **Visualization Nodes**: Create visual representations for Foxglove Studio
4. **Hand Landmark Interpreter**: Converts detected landmarks to joint states
5. **Hand Gesture Interpreter**: Alternative control method using gesture recognition
6. **URDF State Publishers**: Visualize both right and left hands
7. **Foxglove Bridge**: Enables visualization through Foxglove Studio

### demo_physical_hand.launch.py

This launch file extends the virtual hand demo to also control a physical dexterous hand:

```
PIPELINE:
camera → hand landmark estimation → hand landmark/gesture interpreters → urdf visualization + real hand control

TOPIC FLOW:
- Camera publishes: /image_raw
- Hand landmark estimation subscribes to: /image_raw and publishes: /hand_landmark_estimation/bounding_box, /hand_landmark_estimation/hand_landmarks
- Visualization nodes subscribe to landmarks/bbox and publish visualizations
- Hand interpreters subscribe to: /hand_landmark_estimation/hand_landmarks and publish: /joint_states
- URDF publishers use joint states to visualize the hands
- Physical hand controller uses joint states to control the real DexHand
```

Components included in this launch file:
1. **Camera Node**: Captures video input for hand tracking
2. **Hand Landmark Estimation**: Detects hands and extracts landmark points
3. **Visualization Nodes**: Create visual representations for Foxglove Studio
4. **Hand Landmark Interpreter**: Converts detected landmarks to joint states
5. **Hand Gesture Interpreter**: Alternative control method using gesture recognition
6. **URDF State Publishers**: Visualize both right and left hands
7. **Real Hand Control**: Controls physical Inspire RH56 DexHand via serial connection
8. **Foxglove Bridge**: Enables visualization through Foxglove Studio

## Usage

To launch the virtual hands demo:

```bash
ros2 launch rzv_demo_dexhand demo_virtual_hands.launch.py
```

To launch the physical hand control demo:

```bash
ros2 launch rzv_demo_dexhand demo_physical_hand.launch.py [video_device:=/dev/video0] [serial_port:=/dev/ttyUSB0]
```

### Launch Arguments
- `video_device`: Specify the camera device (default: `/dev/video0`)
- `landmark_model_type`: Type of hand landmark model to use (default: `mediapipe_hand_landmark`, others: `rtmpose_hand`, `hrnetv2_hand_landmark`)
- `serial_port`: Serial port for the physical DexHand (default: `/dev/ttyUSB0`, only for `demo_physical_hand.launch.py`)

### Hardware Requirements
- Renesas RZ/V platform
- USB camera for hand tracking
- Inspire RH56 DexHand connected via serial port (for physical hand demo)

### Visualization with Foxglove Studio

The demo can be visualized using Foxglove Studio by connecting to the Foxglove Bridge websocket.

#### Using the Preset Layout

For the best visualization experience, a preset panel layout is provided:

1. Start Foxglove Studio
2. Connect to the Foxglove Bridge websocket (typically `ws://localhost:8765`)
3. Click on "Layouts" in the top menu
4. Select "Import layout from file"
5. Navigate to the `config/foxglove/demo_dexhand.json` file in the rzv_demo_dexhand package
6. Click "Open" to load the preset layout

The preset layout provides:
- Camera view with hand landmark overlays
- 3D visualization of the virtual hands
- Joint state monitoring panels
- Custom panels configured specifically for the dexterous hand demo

This layout ensures all the necessary visualization components are properly set up without manual configuration.

## License
Apache License 2.0
