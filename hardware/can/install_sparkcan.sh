#!/bin/bash
# Install sparkcan library to system
# This must be run with sudo

set -e

# Get the script's directory and navigate to workspace src
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_SRC="$(cd "$SCRIPT_DIR/../../../../" && pwd)"
SPARKCAN_DIR="$WORKSPACE_SRC/sparkcan"

echo "Looking for sparkcan in: $SPARKCAN_DIR"

if [ ! -d "$SPARKCAN_DIR" ]; then
    echo "Error: sparkcan directory not found at $SPARKCAN_DIR"
    echo "Please clone sparkcan first:"
    echo "  cd $WORKSPACE_SRC"
    echo "  git clone https://github.com/grayson-arendt/sparkcan.git"
    exit 1
fi

# Create COLCON_IGNORE to prevent colcon from trying to build sparkcan
if [ ! -f "$SPARKCAN_DIR/COLCON_IGNORE" ]; then
    echo "Creating COLCON_IGNORE file..."
    touch "$SPARKCAN_DIR/COLCON_IGNORE"
    echo "✓ sparkcan will be ignored by colcon build"
fi

# Build if not already built
if [ ! -d "$SPARKCAN_DIR/build" ]; then
    echo "Building sparkcan..."
    cd "$SPARKCAN_DIR"
    mkdir -p build && cd build
    cmake ..
    make -j$(nproc)
fi

cd "$SPARKCAN_DIR/build"

echo "Installing sparkcan library to system..."
make install

echo "✓ sparkcan library installed successfully"
echo ""
echo "Library files installed to:"
echo "  /usr/local/lib/libsparkcan.so"
echo "  /usr/local/include/SparkFlex.hpp"
echo "  /usr/local/include/SparkMax.hpp"
echo "  /usr/local/include/SparkBase.hpp"
echo "  /usr/local/lib/cmake/sparkcan/"
echo ""
echo "You may need to run: sudo ldconfig"
