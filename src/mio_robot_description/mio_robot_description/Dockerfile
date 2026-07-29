FROM ros2_humble_last

# 1. Dipendenze
RUN apt-get update && apt-get install -y \
    python3-pip \
    python3-colcon-common-extensions \
    dos2unix && \
    rm -rf /var/lib/apt/lists/* && \
    pip3 install --no-cache-dir fastapi uvicorn pydantic pyserial requests

# 2. Workspace ROS 2
WORKDIR /ros2_ws/src

# 3. Copia ENTRAMBI i pacchetti
COPY . /ros2_ws/src/

# 4. Compilazione
WORKDIR /ros2_ws
RUN /bin/bash -c "source /opt/ros/humble/setup.bash && colcon build --symlink-install"

# 5. Source automatici
RUN echo "source /opt/ros/humble/setup.bash" >> /root/.bashrc && \
    echo "source /ros2_ws/install/setup.bash" >> /root/.bashrc

WORKDIR /ros2_ws/src/mio_robot_description

EXPOSE 8000

CMD ["tail", "-f", "/dev/null"]