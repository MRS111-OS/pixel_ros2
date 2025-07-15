#!/bin/bash

echo "Copying usb rules to /etc/udev/rules.d/ ..."
sudo cp 99-titan-robot-usb.rules /etc/udev/rules.d/

# Step 2: Reload the udev rules
echo "Reloading udev rules ..."
sudo udevadm control --reload-rules

# Step 3: Trigger udev to apply the changes
echo "Triggering udev ..."
sudo udevadm trigger

# Step 4: Check the permissions of the device
echo "Checking device permissions ..."
ls -l /dev/esp32
ls -l /dev/slidar

echo "Adding the current user: [$(whoami)] to the dialout group ..."
sudo usermod -aG dialout $(whoami)

echo "You may need to log out and log back in for the group changes to take effect."
