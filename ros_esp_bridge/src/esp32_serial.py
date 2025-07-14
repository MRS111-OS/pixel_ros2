#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from geometry_msgs.msg import Quaternion
import serial
import threading
import re
import math

class SerialBridgeNode(Node):
    def __init__(self):
        super().__init__('serial_bridge_node')
        self.ser = serial.Serial('/dev/ttyUSB0', 115200, timeout=0.1)
        self.cmd_vel_sub = self.create_subscription(Twist, 'cmd_vel', self.cmd_vel_callback, 10)
        self.odom_pub = self.create_publisher(Odometry, 'odom', 10)
        self.odom_msg = Odometry()
        self.lock = threading.Lock()
        self.thread = threading.Thread(target=self.read_serial)
        self.thread.daemon = True
        self.thread.start()

    def cmd_vel_callback(self, msg):
        linear = msg.linear.x
        angular = msg.angular.z
        cmd = f"{linear:.2f} {angular:.2f}\n"
        with self.lock:
            self.ser.write(cmd.encode())

    def read_serial(self):
        pos_re = re.compile(r'POS: x=([-\d\.]+) y=([-\d\.]+) theta=([-\d\.]+)')
        while rclpy.ok():
            try:
                line = self.ser.readline().decode(errors='ignore').strip()
                match = pos_re.match(line)
                if line:
                    self.get_logger().info(f"Serial line: {line}")
                if match:
                    x, y, theta = map(float, match.groups())
                    self.odom_msg.pose.pose.position.x = x
                    self.odom_msg.pose.pose.position.y = y
                    # Convert yaw (theta) to quaternion
                    q = self.yaw_to_quaternion(theta)
                    self.odom_msg.pose.pose.orientation.x = q.x
                    self.odom_msg.pose.pose.orientation.y = q.y
                    self.odom_msg.pose.pose.orientation.z = q.z
                    self.odom_msg.pose.pose.orientation.w = q.w
                    self.odom_pub.publish(self.odom_msg)
            except Exception as e:
                self.get_logger().warn(f"Serial read error: {e}")

    def yaw_to_quaternion(self, yaw):
        q = Quaternion()
        q.x = 0.0
        q.y = 0.0
        q.z = math.sin(yaw / 2.0)
        q.w = math.cos(yaw / 2.0)
        return q

def main(args=None):
    rclpy.init(args=args)
    node = SerialBridgeNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()