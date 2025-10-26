# SparkCAN Library Setup

## Why SparkCAN is Not in This Repository

The **sparkcan** library is a third-party C++ library maintained by Grayson Arendt. It is NOT part of this ROS2 package and must be installed separately as a system library.

**Repository**: https://github.com/grayson-arendt/sparkcan

## Quick Setup

### Option 1: Automated (Recommended)

```bash
# 1. Clone sparkcan into your workspace
cd ~/ros2_ws/src
git clone https://github.com/grayson-arendt/sparkcan.git

# 2. Run the install script (builds and installs)
cd ~/ros2_ws/src/lunabot_one
sudo ./hardware/can/install_sparkcan.sh

# 3. Update library cache
sudo ldconfig
```

### Option 2: Manual

```bash
# 1. Clone sparkcan
cd ~/ros2_ws/src
git clone https://github.com/grayson-arendt/sparkcan.git

# 2. Build
cd sparkcan
mkdir -p build && cd build
cmake ..
make -j$(nproc)

# 3. Install to system
sudo make install
sudo ldconfig
```

## Verification

Check if sparkcan is installed correctly:

```bash
# Check if library exists
ls -l /usr/local/lib/libsparkcan.so

# Check if headers exist
ls -l /usr/local/include/SparkFlex.hpp

# Check if CMake config exists
ls -l /usr/local/lib/cmake/sparkcan/
```

Expected output:
```
/usr/local/lib/libsparkcan.so
/usr/local/include/SparkBase.hpp
/usr/local/include/SparkFlex.hpp
/usr/local/include/SparkMax.hpp
/usr/local/lib/cmake/sparkcan/sparkcanConfig.cmake
```

## Git Configuration

The sparkcan library is excluded from this repository via `.gitignore`:

```bash
# Check workspace .gitignore
cat ~/ros2_ws/src/.gitignore
# Should show: sparkcan/
```

**Important**: After cloning sparkcan, it must be ignored by colcon:

```bash
# The install script creates this automatically, but you can also create it manually
touch ~/ros2_ws/src/sparkcan/COLCON_IGNORE
```

This ensures:
- ✅ Your repository stays clean
- ✅ You always use the latest sparkcan version
- ✅ Reduced repository size
- ✅ Proper attribution to original author
- ✅ Colcon won't try to build sparkcan as a ROS2 package

## Updating SparkCAN

To update to the latest version:

```bash
cd ~/ros2_ws/src/sparkcan
git pull
cd build
make clean
cmake ..
make -j$(nproc)
sudo make install
sudo ldconfig
```

## Troubleshooting

### "sparkcan not found" during build

```bash
# Make sure it's installed
ls /usr/local/lib/libsparkcan.so

# If not found, install it
cd ~/ros2_ws/src/lunabot_one
sudo ./hardware/can/install_sparkcan.sh
sudo ldconfig
```

### Build errors in sparkcan

```bash
# Make sure you have dependencies
sudo apt install git cmake build-essential

# Clean build
cd ~/ros2_ws/src/sparkcan
rm -rf build
mkdir build && cd build
cmake ..
make -j$(nproc)
```

### Permission errors

All installation requires sudo:
```bash
sudo make install
sudo ldconfig
```

## Firmware Compatibility

**Critical**: SparkCAN only works with SparkFlex firmware **24.0.X**

- ✅ Firmware 24.0.0 - 24.0.X: Compatible
- ❌ Firmware 25.0.X: NOT compatible

Use REV Hardware Client to:
1. Check current firmware version
2. Downgrade to 24.0.X if needed

## Why This Approach?

### Advantages:
1. **Proper attribution** - Credits original author
2. **Always up-to-date** - Easy to pull latest changes
3. **Clean repository** - No third-party code in your repo
4. **Standard practice** - Common for C++ system libraries

### Comparison to ROS2 Dependencies:

**ROS2 packages** (in package.xml):
```xml
<depend>nav2_bringup</depend>  <!-- Installed via apt -->
```

**System libraries** (in CMakeLists.txt):
```cmake
find_package(sparkcan REQUIRED)  <!-- Installed via make install -->
```

SparkCAN falls into the second category - it's a system library like OpenCV, Eigen, etc.

## License

SparkCAN is maintained by Grayson Arendt and has its own license. Please refer to the [original repository](https://github.com/grayson-arendt/sparkcan) for license details.
