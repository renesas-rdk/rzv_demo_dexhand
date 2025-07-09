# Cross-Compiling the ROS 2 Dexhand Application for RZ/V2H

This guide describes how to build the **ROS 2 Dexhand Application** on the host machine using the Yocto SDK, and deploy the result to the RZ/V2H target board.
## Setup Environment Cross-Compile
Use the provided cross-compilation environment & prebuilt SDK installer file to build your ROS 2 application for the RZ/V2H platform.
- *Clone the crossbuild repository*
    ```bash
    cd <your_workspace>
    git clone <repository_url_for_X_compilation>
    ```
- *Copy prebuilt Yocto SDK to workspace*
    ```bash
    cp poky-*.sh <your_X_compilation_ws>
    ```
- *Setup the ros2 workspace*
     ```bash
    cd <your_X_compilation_ws>
    #Create ros2 workspace
    mkdir -p Dexhand/ros2_ws
    ```
- *Clone all required packages in your workspace*
    ```bash
    cd <your_X_compilation_ws>/Dexhand/ros2_ws
    git clone <repository_url_for_arm_hand_control>
    git clone <repository_url_for_foxglove_keypoint_publisher>
    git clone <repository_url_for_inspire_rh56_urdf>
    git clone <repository_url_for_ruiyan_rh2_controller>
    git clone <repository_url_for_ruiyan_rh2_urdf>
    git clone <repository_url_for_ruiyan_rh2_dexhand>
    git clone <repository_url_for_rzv_demo_dexhand>
    git clone <repository_url_for_rzv_model>
    git clone <repository_url_for_rzv_pose_estimation>
    ```
**Note:**
> Please install git-lfs as some repositories use LFS to store large files.

You should see the following structure:

```
<your_workspace>/
└── <your_X_compilation_ws>/
    ├──Dexhand/
    │    ├── ros2_ws/
    │    │   ├── arm_hand_control/
    │    │   ├── foxglove_keypoint_publisher/
    │    │   ├── inspire_rh56_urdf/
    │    │   ├── inspire_rh56_dexhand/
    │    │   ├── ruiyan_rh2_controller/
    │    │   ├── ruiyan_rh2_urdf/
    │    │   ├── ruiyan_rh2_dexhand/
    │    │   ├── rzv_demo_dexhand/
    │    │   ├── rzv_model/
    │    │   └── rzv_pose_estimation/
    │    └── ...
    ├── toolchain/
    ├── Dockerfile
    ├── poky-*sh
    ├── README.md
    └── ...
```
- *Build the Docker Container*
    ```bash
    cd <your_X_compilation_ws>
    ./setup_ros2_cross_env.sh Dexhand/ [name_of_docker_container]
    ```
- *Access the container shell*
    ```bash
    docker exec -it [name_of_docker_container] /bin/bash
    ```
## Start Compilation

Inside the container, navigate to your ROS 2 workspace:
```bash
# $ROS2_WS: Environment variable for the default ROS 2 workspace directory
cd $ROS2_WS
```
Use the `cross-colcon-build` build to build packages.

`cross-colcon-build` is a wrapper around the standard `colcon build` command that:

- Checks if a `cross.cmake` toolchain file exists in the current working directory.
- Unsets `LD_LIBRARY_PATH` to avoid conflicts with the cross-compilation environment.
- Loads the cross-compilation environment by sourcing the appropriate SDK setup script.
- Runs `colcon build` with the necessary CMake arguments for cross-compilation, along with any user-provided arguments.

### Folder structure
This is the correct folder structure of workspace:
```
ros2_ws
├── build
├── cross.cmake
├── install
│   ├── setup.bash
│   └── ...
├── log
├── arm_hand_control/
├── foxglove_keypoint_publisher/
├── inspire_rh56_urdf/
├── inspire_rh56_dexhand/
├── ruiyan_rh2_controller/
├── ruiyan_rh2_urdf/
├── ruiyan_rh2_dexhand/
├── rzv_demo_dexhand/
├── rzv_model/
├── rzv_pose_estimation/
└── .vscode
    ├── deploy.sh
    ├── launch.json
    ├── run_program.sh
    ├── settings.json
    ├── settings.linux.json
    ├── start_target_gdbserver.sh
    └── tasks.json
```

**Note:**
>Please read repository's `Readme` and `poky-glibc-*.target.manifest` carefully.
It contains detailed instructions and a list of supported ROS 2 packages, as well as the exact steps required to set up and run the cross-compilation process successfully.
## Deployment to target
Deploy the Built Application to RZ/V2H Board
   ```bash
   # Create the destination directory on the target board
   ssh rzpi@192.168.1.10 "mkdir -p /home/rzpi/ros2_ws"

   # Copy the built ROS 2 application to the board via SCP
   scp -r install/ rzpi@192.168.1.10:/home/rzpi/ros2_ws/
   ```
The built workspace (install/) will be transferred to the board at /home/rzpi/ros2_ws/install