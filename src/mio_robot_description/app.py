import time
import threading
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import rclpy
from rclpy.executors import MultiThreadedExecutor
from rclpy.callback_groups import ReentrantCallbackGroup
from moveit_msgs.srv import GetPositionIK
import function as f

client = None
joint_pub = None
node = None
ros_thread = None

class InputData(BaseModel):
    x: float
    y: float
    z: float

@asynccontextmanager
async def lifespan(app: FastAPI):
    global client, joint_pub, node, ros_thread

    # 1. Inizializzazione MoveIt e Nodo
    client, joint_pub, node = f.initMovit()

    # 2. Assegniamo un ReentrantCallbackGroup al client e un MultiThreadedExecutor
    # Questo permette di gestire chiamate concorrenti/consecutive senza blocchi sulla coda
    executor = MultiThreadedExecutor()
    executor.add_node(node)

    def spin_ros():
        executor.spin()

    ros_thread = threading.Thread(target=spin_ros, daemon=True)
    ros_thread.start()

    yield

    if node:
        node.destroy_node()
    if rclpy.ok():
        rclpy.shutdown()

app = FastAPI(lifespan=lifespan)
last_joint_positions = [0.0, 0.0, 0.0, 0.0]

@app.post("/compute")
def sendRequest(data: InputData):
    global last_joint_positions  # Dichiara che userai la variabile globale

    req = GetPositionIK.Request()
    req.ik_request.group_name = 'bottino'
    req.ik_request.ik_link_name = 'tcp'
    req.ik_request.avoid_collisions = True

    req.ik_request.timeout.sec = 1
    req.ik_request.timeout.nanosec = 0

    # 💡 USA LE ULTIME POSIZIONI COME PUNTO DI PARTENZA (Questi ora sono radianti corretti)
    req.ik_request.robot_state.joint_state.name = ['joint0', 'joint1', 'joint2', 'joint3']
    req.ik_request.robot_state.joint_state.position = last_joint_positions

    # POSA TARGET
    req.ik_request.pose_stamped.header.frame_id = 'base'
    req.ik_request.pose_stamped.pose.position.x = data.x
    req.ik_request.pose_stamped.pose.position.y = data.y
    req.ik_request.pose_stamped.pose.position.z = data.z

    req.ik_request.pose_stamped.pose.orientation.x = 0.0
    req.ik_request.pose_stamped.pose.orientation.y = 1.0
    req.ik_request.pose_stamped.pose.orientation.z = 0.0
    req.ik_request.pose_stamped.pose.orientation.w = 0.0

    future = client.call_async(req)

    start_time = time.time()
    max_wait = 5.0

    while not future.done():
        time.sleep(0.02)
        if time.time() - start_time > max_wait:
            break

    risposta = future.result() if future.done() else None

    # 💡 CORREZIONE: Salviamo i radianti originali calcolati da MoveIt
    # Lo facciamo solo se abbiamo ricevuto una risposta e se l'IK ha avuto successo (error_code = 1)
    if risposta is not None and risposta.error_code.val == 1:
        last_joint_positions = list(risposta.solution.joint_state.position)


    # La tua funzione che converte in gradi e fa i controlli
    real_angles = f.checkResponse(risposta, node, joint_pub)

    if real_angles is None:
        raise HTTPException(
            status_code=422,
            detail=f"Impossibile calcolare la cinematica per la posizione x:{data.x} y:{data.y} z:{data.z}"
        )

    # (La vecchia riga "last_joint_positions = list(real_angles)" è stata cancellata da qui)

    return f.checkResult(real_angles)

