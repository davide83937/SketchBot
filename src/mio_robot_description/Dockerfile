FROM ros2_humble_last

# 1. Installiamo le dipendenze di sistema e Python (prima del COPY per sfruttare la cache Docker)
RUN apt-get update && apt-get install -y \
    python3-pip \
    python3-colcon-common-extensions \
    dos2unix && \
    rm -rf /var/lib/apt/lists/* && \
    pip3 install --no-cache-dir fastapi uvicorn pydantic pyserial requests

# 2. Impostiamo la directory di destinazione per il pacchetto ROS 2
WORKDIR /ros2_ws/src/mio_robot_description

# 3. Copiamo I FILE del pacchetto (package.xml, setup.py, app.py, ecc.) nella WORKDIR corrente
COPY . .

# 4. Ci spostiamo alla radice del workspace per la build
WORKDIR /ros2_ws

# 5. Compiliamo il pacchetto ROS 2
RUN /bin/bash -c "source /opt/ros/humble/setup.bash && colcon build --symlink-install"

# 6. Aggiungiamo i source automatici al .bashrc per le sessioni interattive
RUN echo "source /opt/ros/humble/setup.bash" >> /root/.bashrc && \
    echo "source /ros2_ws/install/setup.bash" >> /root/.bashrc

# 7. Ci posizioniamo nella radice DEL PACCHETTO dove risiedono app.py e le risorse
WORKDIR /ros2_ws/src/mio_robot_description

EXPOSE 8000

CMD ["tail", "-f", "/dev/null"]