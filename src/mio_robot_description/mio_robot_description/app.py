#!/usr/bin/env python3
from contextlib import asynccontextmanager

import function as f
import rclpy
from moveit_msgs.srv import GetPositionIK
from sensor_msgs.msg import JointState
from fastapi import FastAPI
from rclpy.executors import SingleThreadedExecutor

from base_model import InputData

# Variabili globali che verranno popolate allo startup
client = None
joint_pub = None
node = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global client, joint_pub, node
    # Inizializziamo ROS 2 e MoveIt solo all'avvio effettivo del server
    client, joint_pub, node = f.initMovit()
    yield
    # (Opzionale) Cleanup alla chiusura
    if node:
        node.destroy_node()

app = FastAPI(lifespan=lifespan)

from moveit_msgs.srv import GetPositionIK
from fastapi import FastAPI, HTTPException
import rclpy


# ... le tue configurazioni e import (app = FastAPI(), ecc.) ...

@app.post("/compute")
def sendRequest(data: InputData):
    req = GetPositionIK.Request()
    req.ik_request.group_name = 'bottino'
    req.ik_request.ik_link_name = 'tcp'
    req.ik_request.avoid_collisions = True
    req.ik_request.timeout.sec = 2

    # Stato iniziale per aiutare il solver KDL a partire da una forma flessa
    req.ik_request.robot_state.joint_state.name = ['joint0', 'joint1', 'joint2', 'joint3']
    # req.ik_request.robot_state.joint_state.position = [1.57, -0.5, 1.0, -0.5]

    # -------------------------------------------------------------
    # POSA TARGET: POSIZIONE + ORIENTAMENTO DRITTO PERPENDICOLARE
    # -------------------------------------------------------------
    req.ik_request.pose_stamped.header.frame_id = 'base'

    # 1. Posizione Cartesiana
    req.ik_request.pose_stamped.pose.position.x = data.x
    req.ik_request.pose_stamped.pose.position.y = data.y
    req.ik_request.pose_stamped.pose.position.z = data.z

    # 2. Orientamento: Quaternione per puntare DRITTO VERSO IL BASSO (Pitch = 180°)
    req.ik_request.pose_stamped.pose.orientation.x = 0.0
    req.ik_request.pose_stamped.pose.orientation.y = 1.0
    req.ik_request.pose_stamped.pose.orientation.z = 0.0
    req.ik_request.pose_stamped.pose.orientation.w = 0.0

    try:
        # Invia la richiesta asincrona al servizio MoveIt IK
        future = client.call_async(req)

        # Al posto di: rclpy.spin_until_future_complete(node, future)
        # Usa questo blocco:
        executor = rclpy.executors.SingleThreadedExecutor()
        executor.add_node(node)
        try:
            executor.spin_until_future_complete(future, timeout_sec=2.0)
        finally:
            executor.remove_node(node)

        if not future.done():
            raise HTTPException(status_code=408, detail="Timeout MoveIt IK")

        risposta = future.result()

        # Elaborazione con le TUE funzioni helper
        real_angles = f.checkResponse(risposta, node, joint_pub)

        if real_angles is None:
            # Se la cinematica fallisce, restituisci un 422 senza far crollare il server
            raise HTTPException(
                status_code=422,
                detail=f"Impossibile calcolare IK per x:{data.x} y:{data.y} z:{data.z}"
            )

        return f.checkResult(real_angles)

    except HTTPException as http_err:
        # Gestisce i fallimenti di IK restituendo l'errore al client HTTP
        raise http_err
    except Exception as e:
        # Se qualcosa va storto nell'elaborazione, evita il crash del thread di Uvicorn
        raise HTTPException(status_code=500, detail=f"Errore interno IK: {str(e)}")

#f.checkResponse(risposta, node, joint_pub)