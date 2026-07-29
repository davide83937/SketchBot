import time
import math
import rclpy
from moveit_msgs.srv import GetPositionIK
from sensor_msgs.msg import JointState


import rclpy
from rclpy.node import Node
from moveit_msgs.srv import GetPositionIK
from sensor_msgs.msg import JointState
from rclpy.callback_groups import ReentrantCallbackGroup

def initMovit():
    # Buona pratica: inizializza rclpy solo se non è già stato inizializzato
    # (Evita crash se FastAPI fa hot-reload durante lo sviluppo)
    if not rclpy.ok():
        rclpy.init()
        
    node = rclpy.create_node('test_ik_node')

    # 1. Creiamo il Callback Group Reentrant
    cb_group = ReentrantCallbackGroup()
    
    # 2. Salviamo il gruppo nel nodo per evitare che il Garbage Collector di Python lo elimini
    node.cb_group = cb_group 

    # 3. ASSEGNIAMO IL GRUPPO AL CLIENT (Il passaggio fondamentale!)
    client = node.create_client(
        GetPositionIK, 
        '/compute_ik', 
        callback_group=cb_group
    )
    
    joint_pub = node.create_publisher(JointState, '/joint_states', 10)
    
    client.wait_for_service()
    
    return client, joint_pub, node



def checkResponse(risposta ,node, joint_pub):
    if risposta is None:
        print(" Nessuna risposta ricevuta da MoveIt (risposta è None).")
        return None
    print("\n-------------------------------------------")
    print("CODICE ERRORE MOVEIT:", risposta.error_code.val)
    real_angles = []
    if risposta.error_code.val == 1:
        names = list(risposta.solution.joint_state.name)
        pos_rad = list(risposta.solution.joint_state.position)
        pos_deg = [math.degrees(p) for p in pos_rad]

        print(" GIUNTI:       ", names)
        print(" ANGOLI (rad): ", [round(p, 4) for p in pos_rad])
        print(" ANGOLI (deg): ", [round(p, 2) for p in pos_deg])
        print("-------------------------------------------\n")

        real_angle_0 = 100 - pos_deg[0]
        real_angle_1 = 93 - pos_deg[1]
        real_angle_2 = 75 - pos_deg[2]
        real_angle_3 = 171 - pos_deg[3]
        real_angles = [real_angle_0, real_angle_1, real_angle_2, real_angle_3]

        msg = JointState()
        msg.name = names
        msg.position = pos_rad

        msg.header.stamp = node.get_clock().now().to_msg()

        # PUBBLICAZIONE: Pubblichiamo un paio di volte per sicurezza e poi usciamo subito
        for _ in range(3):
            joint_pub.publish(msg)
            time.sleep(0.01)

        print("Posizione e Orientamento Dritti Raggiunti e pubblicati!")

    else:
        print(" FALLITO CON CODICE:", risposta.error_code.val)
        print(" (Se fallisce, la posizione Z/Y è troppo lontana o l'orientamento viola i limiti dei giunti)")
        print("-------------------------------------------\n")

    return real_angles

def checkResult(angles):
    if len(angles)==0:
        return {
            "status": "failure",
            "output": angles
        }
    if len(angles)>0:
        return {
            "status": "success",
            "output": angles
        }

