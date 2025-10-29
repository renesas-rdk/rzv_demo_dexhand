# RZ/V Demo DexHand

This package provides launch files and configurations for demonstrating dexterous hand control on Renesas RZ/V platforms. It integrates vision-based pose estimation with both virtual and physical hand control.

## Overview

The RZ/V Demo DexHand package enables:
- Hand landmark estimation and interpretation
- Simultaneous control of virtual and physical dexterous hands
- Support visualization through Foxglove Studio

## RZ/V ROS2 Package Dependencies

| Category | Package Name | Description |
|-----------|---------------|-------------|
| **Base Packages** | `arm_hand_control` | Core control logic for the dexterous hand. |
|  | `foxglove_keypoint_publisher` | Publishes keypoints for visualization in Foxglove Studio. |
|  | `rzv_demo_dexhand` | Main demo package integrating DexHand functionalities on RZ/V platform. |
|  | `rzv_model` | Contains model definitions and configuration files for the RZ/V system. |
|  | `rzv_pose_estimation` | Provides pose estimation capabilities on Renesas RZ/V platforms. |
| **For Inspire RH56 DexHand Demo** | `inspire_rh56_urdf` | URDF models for the Inspire RH56 dexterous hand. |
|  | `inspire_rh56_dexhand` | Application and control logic for the Inspire RH56 hand. |
| **For Ruiyan RH2 DexHand Demo** | `ruiyan_rh2_controller` | Control package for the Ruiyan RH2 dexterous hand. |
|  | `ruiyan_rh2_urdf` | URDF models for the Ruiyan RH2 hand. |
|  | `ruiyan_rh2_dexhand` | Control node for the Ruiyan RH2 hand. |

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
For detailed instructions, refer to the corresponding dexhand package for each hand type.
### Run the Demo

To launch the virtual hands demo:

```bash
# For Inspire RH56 hand
ros2 launch rzv_demo_dexhand demo_virtual_inspire_rh56_hands.launch.py

# For Ruiyan RH2 hand
ros2 launch rzv_demo_dexhand demo_virtual_ruiyan_rh2_hands.launch.py
```

To launch the physical Inspire RH56 hand control demo:

```bash
ros2 launch rzv_demo_dexhand demo_physical_inspire_rh56_hand.launch.py video_device:=/dev/video0 serial_port:=/dev/ttyUSB0
```

To launch the physical RuiYan RH2 hand control demo:

```bash
ros2 launch rzv_demo_dexhand demo_physical_ruiyan_rh2_hand.launch.py video_device:=/dev/video0 can_port:=can2
```

### Demo operation

Based on your hand gesture shown in front of the camera, the dexterous hand will mimic your hand movements.

### Launch Arguments
- `video_device`: Specify the camera device (default: `/dev/video0`)
- `landmark_model_type`: Type of hand landmark model to use (default: `mediapipe_hand_landmark`, others: `rtmpose_hand`, `hrnetv2_hand_landmark`)
- `serial_port`: Serial port for the physical Inspire RH56 DexHand (default: `/dev/ttyUSB0`, only for `demo_physical_hand.launch.py`)
- `can_port`: Can port for the physical RuiYan RH2 DexHand (default: `can2`, only for `demo_physical_ruiyan_rh2_hand.launch.py`)


## Launch Files

#### demo_virtual_inspire_rh56_hands.launch.py and demo_virtual_ruiyan_rh2_hands.launch.py

This launch file sets up a camera-based hand tracking system that controls virtual Inspire RH56 hands or Ruiyan RH2 hands:

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

#### demo_physical_inspire_rh56_hand.launch.py

This launch file extends the virtual hand demo to also control a physical Inspire RH56 dexterous hand:

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

#### demo_physical_ruiyan_rh2_hand.launch.py

This launch file extends the virtual hand demo to also control a physical RuiYan RH2 dexterous hand:

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
- Ruiyan RH2 DexHand: Perform message conversion: subscribes to /joint_states, publishes /ryhand6_cmd
- Physical hand controller: subscribes to /ryhand6_cmd to control the real DexHand


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
