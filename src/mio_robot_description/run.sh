#!/bin/bash
set -e

source /opt/ros/humble/setup.bash

if [ -f /root/workspace/install/setup.bash ]; then
    source /root/workspace/install/setup.bash
fi

exec uvicorn app:app --host 0.0.0.0 --port 8000
