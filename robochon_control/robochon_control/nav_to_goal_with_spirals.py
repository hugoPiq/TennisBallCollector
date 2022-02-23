import os

import numpy as np

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import PointCloud2
from geometry_msgs.msg import PoseStamped, Twist
import tf2_py
from nav2_msgs.action import NavigateToPose


def angle(v):
    x, y = v.flatten()
    return np.arctan2(y, x)


def to_euler(q):
    angles = [0, 0, 0]

    sinr_cosp = 2 * (q.w * q.x + q.y * q.z)
    cosr_cosp = 1 - 2 * (q.x * q.x + q.y * q.y)
    angles[0] = np.arctan2(sinr_cosp, cosr_cosp)

    sinp = 2 * (q.w * q.y - q.z * q.x)
    if abs(sinp) >= 1:
        angles[1] = np.pi / 2 * np.sign(sinp)
    else:
        angles[1] = np.arcsin(sinp)

    siny_cosp = 2 * (q.w * q.z + q.x * q.y)
    cosy_cosp = 1 - 2 * (q.y * q.y + q.z * q.z)
    angles[2] = np.arctan2(siny_cosp, cosy_cosp)

    return angles

    
class Navigator(Node):

    def __init__(self):
        super().__init__("navigator")

        self.position = PoseStamped()
        self.target_position = PoseStamped()

        self.spiral_center = np.zeros((2, 1))

        self.command = Twist()

        self.create_subscription(PoseStamped, "goal_pose", self.target_goal_callback, 10)
        self.create_subscription(PoseStamped, "robot_pose", self.robot_pose_callback, 10)

        self.create_timer(0.1, self.timer_callback)

    def target_goal_callback(self, msg):
        self.target_position = msg

    def robot_pose_callback(self, msg):
        self.position = msg

    def timer_callback(self):
        q = self.position.pose.orientation
        r = to_euler(q)
        robot_state = np.array([[self.position.pose.position.x],
                                [self.position.pose.position.y],
                                [r[2]]])

        q = self.target_position.pose.orientation
        r = to_euler(q)
        target_state = np.array([[self.target_position.pose.position.x],
                                [self.target_position.pose.position.y],
                                [r[2]]])

        beta = angle(robot_state[:2] - self.spiral_center)
        alpha = angle(np.array([[np.cos(robot_state[2, 0])], [np.sin(robot_state[2, 0])]]) - (self.spiral_center - robot_state[:2]))
        print(alpha)


def main():
    rclpy.init()
    node = Navigator()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        print("Clean stop.")
    # except BaseException as e:
    #     print(f"Node error : {e}")
    finally:
        node.destroy_node()
        rclpy.shutdown()
