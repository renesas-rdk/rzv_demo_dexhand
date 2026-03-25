# RZ/V Demo DexHand

This package provides launch files and configurations for demonstrating dexterous hand control on Renesas RZ/V platforms. It integrates vision-based pose estimation with both virtual and physical hand control.

## Overview

The RZ/V Demo DexHand package enables:
- Hand landmark estimation and interpretation
- Simultaneous control of virtual and physical dexterous hands
- Support visualization through Foxglove Studio

## RZ/V ROS2 Package Dependencies

### Base Packages
| Package Name | Description |
|---------------|-------------|
| `arm_hand_control` | Core control logic for the dexterous hand. |
| `foxglove_keypoint_publisher` | Publishes keypoints for visualization in Foxglove Studio. |
| `rzv_demo_dexhand` | Main demo package integrating DexHand functionalities on RZ/V platform. |

### Model Zoo

#### Base Models
| Package Name | Description |
|---------------|-------------|
| `rzv_model` | AI model abstractions and implementations for RZ/V MPU platforms. |
| `rzv_model_utils_ros2` | Collection of helper functions for integrating AI models into ROS 2 applications. |

#### Hand Models
| Package Name | Description |
|---------------|-------------|
| `rzv_yolox` | YOLOX object detection models optimized for RZ/V processors with DRP-AI acceleration. |

#### Landmark Models
| Package Name | Description |
|---------------|-------------|
| `rzv_mediapipe` | MediaPipe-based pose detection models optimized for RZ/V with DRP-AI support. |
| `rzv_rtmpose` | RTMPose-based pose detection models optimized for RZ/V with DRP-AI support. |
| `rzv_hrnetv2` | HRNetV2-based pose detection models optimized for RZ/V with DRP-AI support. |

#### Application
| Package Name | Description |
|---------------|-------------|
| `rzv_pose_estimation` | Pose estimation capabilities for RZ/V platforms. |

### Inspire RH56 Hand Packages

| Package Name | Description |
|--------------|-------------|
| `inspire_rh56_hand_description` | URDF and mesh models for the Inspire RH56 dexterous hand. |
| `inspire_rh56_hand_ros2_control` | ros2_control configuration and hardware interface for the Inspire RH56 hand. |
| `inspire_rh56_hand_bringup` | Launch files to start the Inspire RH56 hand system, including controllers and visualization. |

### Ruiyan RH2 DexHand Demo
| Package Name | Description |
|--------------|-------------|
| `ruiyan_rh2_hand_description` | URDF and mesh models for the Ruiyan RH2 dexterous hand. |
| `ruiyan_rh2_hand_ros2_control` | ros2_control configuration and hardware interface for the Ruiyan RH2 hand. |
| `ruiyan_rh2_hand_bringup` | Launch files to start the Ruiyan RH2 hand system, including controllers and visualization. |

## Prerequisites
### Hardware Requirements:
- USB camera for hand tracking
- Optional: Inspire RH56 DexHand (for physical hand demo)
- Optional: RuiYan RH2 DexHand (for physical hand demo)

## Quick Setup Guide
### Build the dexhand demo application

Install the packages listed in [RZ/V ROS2 Package Dependencies](#rzv-ros2-package-dependencies) and refer to the **ROS2 Application Development/Cross-build the ROS2 Application** in the **RZ/V2H Robotic Development Kit User Manual** documentation to build and compile and deploy them.

Additionally, **native builds using `colcon`** are still supported.

For more details, please refer to the official ROS 2 guide: [Using colcon to build packages](https://docs.ros.org/en/jazzy/Tutorials/Beginner-Client-Libraries/Colcon-Tutorial.html)

### Install the package dependencies
After completing Step 2 above, deploy the `install` folder to the target board if you are using the cross-build method.

Use `rosdep` to install all required dependencies on the target board:
```bash
# Chane the directory to your ROS2 workspace
cd <your_ros2_ws>

# Install dependencies for the following common packages
rosdep install --from-paths install/*/share -y -r --ignore-src
```

### Load the workspace
You must source the setup script to make the packages visible to ROS:
```bash
# Source ROS2 in the current shell
source /opt/ros/jazzy/setup.bash

source install/setup.bash
```

## Run the DexHand demo
### Connect and setup hardware

Connect the USB camera to the RZ/V2H RDK board.

**Optional:** Connect the dexterous hand to the RZ/V2H RDK board if you want to control the real hand.

**Note**: Before running the demo application, please make sure to set up the hardware using the provided setup script.
For detailed instructions, refer to the corresponding hand_bringup package for each hand type.
### Run the Demo

To launch the virtual hands demo:

```bash
# For Inspire RH56 hand
ros2 launch rzv_demo_dexhand demo_inspire_rh56_hand.launch.py use_mock_hardware:=true

# For Ruiyan RH2 hand
ros2 launch rzv_demo_dexhand demo_ruiyan_rh2_hand.launch.py use_mock_hardware:=true
```

To launch the physical Inspire RH56 hand control demo:

```bash
ros2 launch rzv_demo_dexhand demo_inspire_rh56_hand.launch.py use_mock_hardware:=false video_device:=/dev/video0 serial_port:=/dev/ttyUSB0
```

To launch the physical RuiYan RH2 hand control demo:

```bash
ros2 launch rzv_demo_dexhand demo_ruiyan_rh2_hand.launch.py use_mock_hardware:=false video_device:=/dev/video0 can_port:=can2
```

### Demo operation

Based on your hand gesture shown in front of the camera, the dexterous hand will mimic your hand movements.

### Launch Arguments
- `video_device`: Specify the camera device (default: `/dev/video0`)
- `landmark_model_type`: Type of hand landmark model to use (default: `mediapipe_hand_landmark`, others: `rtmpose_hand`, `hrnetv2_hand_landmark`)
- `serial_port`: Serial port for the physical Inspire RH56 DexHand (default: `/dev/ttyUSB0`, only for `demo_physical_hand.launch.py`)
- `can_port`: Can port for the physical RuiYan RH2 DexHand (default: `can2`, only for `demo_ruiyan_rh2_hand.launch.py`)
- `use_mock_hardware`: Set to "true" for simulation/testing without physical hardware

## Launch Files
 
### demo_inspire_rh56_hand.launch.py
 
This launch file extends the virtual hand demo to also control a physical Inspire RH56 dexterous hand:
 
```
PIPELINE:
camera → hand landmark estimation → hand landmark/gesture interpreters
  → ros2_control position controller → joint_state_broadcaster → urdf visualization + real hand control
 
TOPIC FLOW:
- Camera publishes: /image_raw
- Hand landmark estimation subscribes to: /image_raw
  publishes: /hand_landmark_estimation/bounding_box, /hand_landmark_estimation/hand_landmarks
- Visualization nodes subscribe to landmarks/bbox and publish: /bbox_visualization, /landmarks_visualization
- Hand interpreters subscribe to: /hand_landmark_estimation/hand_landmarks
  publish: /inspire_rh56_hand_joint_position_controller/commands
- ros2_control position controller subscribes to: /inspire_rh56_hand_joint_position_controller/commands
- joint_state_broadcaster publishes: /joint_states
- URDF publishers subscribe to: /joint_states for hand visualization
```
 
Components included in this launch file:
1. **Robot Bringup** (`inspire_rh56_hand_bringup`): Initializes ros2_control with the Inspire RH56 joint position controller and joint state broadcaster; connects to the physical hand via serial port
2. **Camera Node**: Captures video input for hand tracking via V4L2
3. **Hand Landmark Estimation**: Detects hands and extracts landmark points from the camera feed
4. **Visualization Nodes**: Create bounding box and landmark visual representations for Foxglove Studio
5. **Hand Gesture Interpreter**: Controls the hand using discrete gesture recognition
6. **Hand Landmark Interpreter**: Alternative control method mapping continuous landmark positions directly to joint commands
 
### demo_ruiyan_rh2_hand.launch.py
 
This launch file extends the virtual hand demo to also control a physical RuiYan RH2 dexterous hand:
 
```
PIPELINE:
camera → hand landmark estimation → hand landmark/gesture interpreters
  → ros2_control position controller → joint_state_broadcaster → urdf visualization + real hand control
 
TOPIC FLOW:
- Camera publishes: /image_raw
- Hand landmark estimation subscribes to: /image_raw
  publishes: /hand_landmark_estimation/bounding_box, /hand_landmark_estimation/hand_landmarks
- Visualization nodes subscribe to landmarks/bbox and publish: /bbox_visualization, /landmarks_visualization
- Hand interpreters subscribe to: /hand_landmark_estimation/hand_landmarks
  publish: /ruiyan_rh2_hand_joint_position_controller/commands
- ros2_control position controller subscribes to: /ruiyan_rh2_hand_joint_position_controller/commands
- joint_state_broadcaster publishes: /joint_states
- URDF publishers subscribe to: /joint_states for hand visualization
```
 
Components included in this launch file:
1. **Robot Bringup** (`ruiyan_rh2_hand_bringup`): Initializes ros2_control with the RuiYan RH2 joint position controller and joint state broadcaster; connects to the physical hand via CAN interface
2. **Camera Node**: Captures video input for hand tracking via V4L2
3. **Hand Landmark Estimation**: Detects hands and extracts landmark points from the camera feed
4. **Visualization Nodes**: Create bounding box and landmark visual representations for Foxglove Studio
5. **Hand Gesture Interpreter**: Controls the hand using discrete gesture recognition
6. **Hand Landmark Interpreter**: Alternative control method mapping continuous landmark positions directly to joint commands

## Visualization with Foxglove Studio

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

#### Demo Visualization

![Foxglove Studio Demo visualization for DexHand](images/demo_dexhand.jpg)

The image above shows the Foxglove Studio interface with the preset layout loaded, displaying the camera feed with hand landmark overlays and the 3D visualization of the virtual hands.

#### Troubleshooting

- Palm Orientation Matters: For optimal detection, make sure the front of the palm faces the camera directly and vertically. Angled hands may reduce accuracy.
- Image Lag in Foxglove Studio: If you experience lag or frozen image streams, simply restart Foxglove Studio.
- 3D Hand Model Not Showing: Sometimes, the 3D hand visualization may not appear properly. In such cases, restart the application (either the demo app or visualization tool).

## License
Apache License 2.0
