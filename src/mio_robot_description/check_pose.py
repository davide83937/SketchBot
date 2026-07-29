#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from moveit_msgs.srv import GetPositionFK
from moveit_msgs.msg import RobotState
from sensor_msgs.msg import JointState


class CheckCurrentPose(Node):
    def __init__(self):
        super().__init__('check_pose_node')
        self.fk_client = self.create_client(GetPositionFK, '/compute_fk')

        self.get_logger().info('In attesa del servizio /compute_fk...')
        if not self.fk_client.wait_for_service(timeout_sec=5.0):
            self.get_logger().error('Servizio /compute_fk non disponibile!')
            return

    def get_fk(self):
        req = GetPositionFK.Request()
        req.header.frame_id = 'base'
        req.fk_link_names = ['end_effector']

        # Impostiamo i giunti a 0 per capire dove si trova la punta in posizione di riposo
        robot_state = RobotState()
        robot_state.joint_state.name = ['joint0', 'joint1', 'joint2', 'joint3']
        robot_state.joint_state.position = [0.0, 0.0, 0.0, 0.0]
        req.robot_state = robot_state

        future = self.fk_client.call_async(req)
        rclpy.spin_until_future_complete(self, future)

        res = future.result()
        if res and res.error_code.val == 1:
            pose = res.pose_stamped[0].pose
            self.get_logger().info('=============================================')
            self.get_logger().info(' COORDINATE REALI CON GIUNTI A ZERO (0,0,0,0):')
            self.get_logger().info(f'  X: {pose.position.x:.4f}')
            self.get_logger().info(f'  Y: {pose.position.y:.4f}')
            self.get_logger().info(f'  Z: {pose.position.z:.4f}')
            self.get_logger().info('=============================================')
            return pose.position.x, pose.position.y, pose.position.z
        else:
            self.get_logger().error('Impossibile calcolare la cinematica diretta.')
            return None


def main():
    rclpy.init()
    node = CheckCurrentPose()
    node.get_fk()
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()