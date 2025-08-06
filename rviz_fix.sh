#!/bin/bash
export QT_OPENGL=desktop
export LIBGL_ALWAYS_SOFTWARE=0
export MESA_GL_VERSION_OVERRIDE=3.3
rviz2 "$@"