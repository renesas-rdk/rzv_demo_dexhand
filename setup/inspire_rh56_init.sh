#!/bin/bash
# This script initializes the Inspire RH56 hardware for the dexhand demo.
# Hardware used: Inspire RH56 dexhand.
# Input:
# - None
# Usage: ./inspire_rh56_init.sh

### Common setup ###
# Map of modules to build: CONFIG_MAP[config_name]="module_name"
declare -A CONFIG_MAP

# User need to find the module names for their hardware setup.
# Syntax: CONFIG_MAP[<CONFIG_NAME>]="<module-name>"

# Dependencies are getted from: https://www.kernelconfig.io/config_can_gs_usb?q=&kernelversion=6.10.14&arch=arm64
CONFIG_MAP[CONFIG_CAN_GS_USB]="gs_usb"
# CONFIG_CAN_DEV already built-in
# CONFIG_CAN_NETLINK already built-in
# CONFIG_NETDEVICES already built-in
# CONFIG_USB already built-in

# Dependencies are getted from: https://www.kernelconfig.io/config_usb_serial?q=&kernelversion=6.10.14&arch=arm64
CONFIG_MAP[CONFIG_USB_SERIAL]="usbserial"
# CONFIG_TTY already built-in
# CONFIG_USB already built-in
# CONFIG_USB_SUPPORT already built-in

# Dependencies are getted from: https://www.kernelconfig.io/config_usb_serial_ch341?q=&kernelversion=6.10.14&arch=arm64
CONFIG_MAP[CONFIG_USB_SERIAL_CH341]="ch341"
# CONFIG_USB already built-in
CONFIG_MAP[CONFIG_USB_SERIAL]="usbserial"
# CONFIG_USB_SUPPORT already built-in

# Dependencies are getted from: https://www.kernelconfig.io/config_usb_serial_cp210x?q=&kernelversion=6.10.14&arch=arm64
CONFIG_MAP[CONFIG_USB_SERIAL_CP210X]="cp210x"
# CONFIG_USB already built-in
# CONFIG_USB_SERIAL duplicate with line above
# CONFIG_USB_SUPPORT already built-in

# === Check if modules are already built-in ===
for config in "${!CONFIG_MAP[@]}"; do
    module="${CONFIG_MAP[$config]}"

    # Check if module is built-in
    if zcat /proc/config.gz | grep -Eq "^${config}=(y)"; then
        echo "Module $module is built into the kernel."
        unset CONFIG_MAP[$config]
    fi
done

# === Load the modules ===
for config in "${!CONFIG_MAP[@]}"; do
    value="${CONFIG_MAP[$config]}"
    module="${value##* }"

    sudo modprobe "$module"
    if [ $? -ne 0 ]; then
        echo "Failed to load module $module. Please verify that the module exists!"
        exit 1
    fi
    echo "Module $module loaded successfully."
done

### Hardware specific setup: Inspire RH56 dexhand###
# Add your user to the dialout group to enable access to /dev/ttyUSBx
if groups $USER | grep -qw dialout; then
    echo "User $USER is already in the dialout group."
else
    sudo usermod -a -G dialout $USER
    echo
    echo "Please log out and log back in to apply the group changes."
fi

