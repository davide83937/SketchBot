#!/usr/bin/env python3
import time
import rclpy
from rclpy.node import Node
from moveit_msgs.srv import GetPositionIK
from moveit_msgs.msg import PositionIKRequest
from geometry_msgs.msg import PoseStamped
from sensor_msgs.msg import JointState


class MoveRobotIK(Node):
    def __init__(self):
        super().__init__('move_robot_ik_script')
        self.ik_client = self.create_client(GetPositionIK, '/compute_ik')
        self.joint_pub = self.create_publisher(JointState, '/joint_states', 10)

        self.get_logger().info('Connessione a /compute_ik...')
        if not self.ik_client.wait_for_service(timeout_sec=5.0):
            self.get_logger().error('Servizio /compute_ik non disponibile!')
            return

    def move_to_xyz(self, x, y, z):
        req = PositionIKRequest()
        req.group_name = 'bottino'
        req.ik_link_name = 'end_effector'

        # DISABILITIAMO IL CONTROLLO COLLISIONI PER TESTARE LA CINEMATICA PURA
        req.avoid_collisions = False
        req.timeout.sec = 2

        # Passiamo lo Start State fittizio
        req.robot_state.joint_state.name = ['joint0', 'joint1', 'joint2', 'joint3']
        req.robot_state.joint_state.position = [0.0, 0.0, 0.0, 0.0]

        target_pose = PoseStamped()
        target_pose.header.frame_id = 'base'
        target_pose.header.stamp = self.get_clock().now().to_msg()
        target_pose.pose.position.x = float(x)
        target_pose.pose.position.y = float(y)
        target_pose.pose.position.z = float(z)
        target_pose.pose.orientation.w = 1.0

        req.pose_stamped = target_pose
        srv_req = GetPositionIK.Request()
        srv_req.ik_request = req

        self.get_logger().info(f'Richiesta IK (No Collision Checking) -> X: {x}, Y: {y}, Z: {z}')
        future = self.ik_client.call_async(srv_req)
        rclpy.spin_until_future_complete(self, future)

        res = future.result()

        if res and res.error_code.val == 1:
            self.get_logger().info(' SUCCESS! Cinematica Inversa calcolata!')
            joint_names = list(res.solution.joint_state.name)
            joint_positions = list(res.solution.joint_state.position)

            self.get_logger().info('--- GIUNTI CALCOLATI ---')
            for name, pos in zip(joint_names, joint_positions):
                self.get_logger().info(f' > {name}: {pos:.4f} rad')

            msg = JointState()
            msg.name = joint_names
            msg.position = joint_positions

            start_time = time.time()
            while time.time() - start_time < 3.0:
                msg.header.stamp = self.get_clock().now().to_msg()
                self.joint_pub.publish(msg)
                time.sleep(0.03)

            self.get_logger().info(' Robot posizionato su RViz!')
        else:
            code = res.error_code.val if res else 'N/A'
            self.get_logger().error(f' FAILED! Codice Errore: {code}')


def main():
    rclpy.init()
    node = MoveRobotIK()

    # Proviamo un punto leggermente sollevato e traslato
    node.move_to_xyz(x=0.05, y=0.05, z=0.25)

    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()