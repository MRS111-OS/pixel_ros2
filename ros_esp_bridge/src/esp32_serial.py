#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist, Quaternion, TransformStamped
from nav_msgs.msg import Odometry
from tf2_ros import TransformBroadcaster
import serial
import threading
import re
import math

class SerialBridgeNode(Node):
    def __init__(self):
        super().__init__('serial_bridge_node')

        # Serial port setup
        self.ser = serial.Serial('/dev/esp32', 115200, timeout=0.1)

        # ROS2 interfaces
        self.cmd_vel_sub = self.create_subscription(Twist, 'cmd_vel', self.cmd_vel_callback, 10)
        self.odom_pub = self.create_publisher(Odometry, 'odom', 10)
        self.tf_broadcaster = TransformBroadcaster(self)

        # Odometry message
        self.odom_msg = Odometry()
        self.lock = threading.Lock()

        # Start serial reading thread
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
                if not line:
                    continue
                self.get_logger().debug(f"Received: {line}")

                match = pos_re.match(line)
                if match:
                    x, y, theta = map(float, match.groups())
                    now = self.get_clock().now().to_msg()

                    # Populate Odometry message
                    self.odom_msg.header.stamp = now
                    self.odom_msg.header.frame_id = "odom"
                    self.odom_msg.child_frame_id = "base_footprint"
                    self.odom_msg.pose.pose.position.x = x
                    self.odom_msg.pose.pose.position.y = y
                    self.odom_msg.pose.pose.position.z = 0.0

                    q = self.yaw_to_quaternion(theta)
                    self.odom_msg.pose.pose.orientation = q

                    self.odom_pub.publish(self.odom_msg)

                    # Broadcast TF transform from odom -> base_footprint
                    t = TransformStamped()
                    t.header.stamp = now
                    t.header.frame_id = "odom"
                    t.child_frame_id = "base_footprint"
                    t.transform.translation.x = x
                    t.transform.translation.y = y
                    t.transform.translation.z = 0.0
                    t.transform.rotation = q

                    self.tf_broadcaster.sendTransform(t)
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
