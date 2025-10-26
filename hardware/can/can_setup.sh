#!/bin/bash

# CAN interface setup script for Raspberry Pi 5 with CAN HAT
# This script sets up the CAN interface for SparkFlex communication

set -e

CAN_INTERFACE="can0"
CAN_BITRATE="1000000"  # 1 Mbps - SparkFlex default

echo "Setting up CAN interface: $CAN_INTERFACE"

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Please run as root (use sudo)"
    exit 1
fi

# Bring down interface if it exists
if ip link show $CAN_INTERFACE > /dev/null 2>&1; then
    echo "Bringing down existing $CAN_INTERFACE interface..."
    ip link set down $CAN_INTERFACE
fi

# Configure CAN interface
echo "Configuring $CAN_INTERFACE with bitrate $CAN_BITRATE..."
ip link set $CAN_INTERFACE type can bitrate $CAN_BITRATE restart-ms 1000
ip link set up $CAN_INTERFACE

# Verify interface is up
if ip link show $CAN_INTERFACE | grep -q "UP"; then
    echo "✓ CAN interface $CAN_INTERFACE is UP and ready"
    echo "✓ Bitrate: $CAN_BITRATE bps"
    
    # Show interface details
    ip -details link show $CAN_INTERFACE
else
    echo "✗ Failed to bring up CAN interface"
    exit 1
fi

# Set proper permissions for CAN access
echo "Setting CAN permissions..."
chmod 666 /dev/can*

echo "CAN setup complete!"
echo ""
echo "To test CAN communication:"
echo "  candump $CAN_INTERFACE          # Monitor CAN traffic"
echo "  cansend $CAN_INTERFACE 123#DEADBEEF  # Send test message"