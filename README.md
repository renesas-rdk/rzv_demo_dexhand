# RZ/V Demo DexHand

This package provides launch files and configurations for demonstrating dexterous hand control on Renesas RZ/V platforms. It integrates vision-based pose estimation with both virtual and physical hand control.

## Overview

The RZ/V Demo DexHand package enables:
- Hand gesture recognition and interpretation
- Simultaneous control of virtual and physical dexterous hands
- Visualization through Foxglove Studio

## Dependencies

### Vision and Perception
- `rzv_pose_estimation`: Provides pose estimation capabilities on Renesas RZ/V platforms
- `v4l2_camera`: Camera interface for video capture
- `foxglove_keypoint_publisher`: Publishes keypoints for visualization

### Hand Control and Visualization
- `arm_hand_control`: Core control logic for the dexterous hand
- `inspire_rh56_urdf`: URDF models for the Inspire RH56
- `robot_state_publisher`: Publishes TF information based on joint states
- `tf2_ros`: Transform library for coordinate frames

### Visualization Bridge
- `foxglove_bridge`: Bridges ROS 2 to Foxglove Studio for visualization

## Launch Files

### gesture_to_physical_and_virtual_hands.launch.py

This launch file sets up a complete pipeline from hand gesture recognition to physical and virtual hand control:

```
PIPELINE:
gesture command → hand interpreter → urdf visualization + real hand control

TOPIC FLOW:
- External source publishes: /hand_gesture
- Hand interpreter subscribes to: /hand_gesture and publishes: /joint_states
- URDF publishers use joint states to visualize both hands
- Real hand controller uses joint states to control physical hand
```

Components included in this launch file:
1. **Hand Gesture Interpreter**: Converts gesture commands to joint states
2. **URDF State Publishers**: Visualize both right and left hands
3. **Common Camera Reference Frame**: Places hands in a shared coordinate system
4. **Real Hand Control**: Controls physical Inspire RH56 DexHand via serial connection
5. **Foxglove Bridge**: Enables visualization through Foxglove Studio

### vision_to_physical_and_virtual_hands.launch.py

This launch file sets up a vision-based hand tracking system that controls both virtual and physical hands:

```
PIPELINE:
camera → hand landmark estimation → hand control → urdf visualization + real hand control

TOPIC FLOW:
- Camera publishes: /image_raw
- Hand landmark estimation subscribes to: /image_raw and publishes: /hand_landmark_estimation/bounding_box, /hand_landmark_estimation/hand_landmarks
- Visualization nodes subscribe to landmarks/bbox and publish visualizations
- Hand interpreter subscribes to: /hand_landmark_estimation/hand_landmarks and publishes: /joint_states
- URDF publishers use joint states to visualize the hands
- Real hand controller uses joint states to control physical hand
```

Components included in this launch file:
1. **Camera Node**: Captures video input for hand tracking
2. **Hand Landmark Estimation**: Detects hands and extracts landmark points
3. **Visualization Nodes**: Create visual representations for Foxglove Studio
4. **Hand Landmark Interpreter**: Converts detected landmarks to joint states
5. **URDF State Publishers**: Visualize both right and left hands
6. **Real Hand Control**: Controls physical Inspire RH56 DexHand via serial connection
7. **Foxglove Bridge**: Enables visualization through Foxglove Studio

## Usage

To launch the gesture-based hand control demo:

```bash
ros2 launch rzv_demo_dexhand gesture_to_physical_and_virtual_hands.launch.py
```

To launch the vision-based hand tracking and control demo:

```bash
ros2 launch rzv_demo_dexhand vision_to_physical_and_virtual_hands.launch.py
```

### Hardware Requirements
- Renesas RZ/V platform
- USB camera for gesture recognition
- Inspire RH56 DexHand connected via serial port (default: /dev/ttyUSB0)

### Visualization
The demo can be visualized using Foxglove Studio by connecting to the Foxglove Bridge websocket.

## License
Apache License 2.0
