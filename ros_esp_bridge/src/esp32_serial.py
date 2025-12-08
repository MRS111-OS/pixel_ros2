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
import time

class SerialBridgeNode(Node):
    def __init__(self):
        super().__init__('esp32_serial_pub_sub')

        self.declare_parameter('serial_port', '/dev/esp32')
        self.declare_parameter('baud_rate', 115200)

        port = self.get_parameter('serial_port').value
        baud = self.get_parameter('baud_rate').value

        self.ser = None

        # create the lock before any serial writes (send_restart uses it)
        self.lock = threading.Lock()

        self.connect_serial(port, baud)

        # send RESTART to the device immediately after connecting
        try:
            self.send_restart()
        except Exception as e:
            self.get_logger().warn(f"Failed to send RESTART on startup: {e}")

        self.cmd_vel_sub = self.create_subscription(Twist, 'cmd_vel', self.cmd_vel_callback, 10)
        self.odom_pub = self.create_publisher(Odometry, 'odom', 10)
        self.tf_broadcaster = TransformBroadcaster(self)

        self.odom_msg = Odometry()

        self.running = True

        self.lines_received = 0

        self.thread = threading.Thread(target=self.read_serial)
        self.thread.daemon = True
        self.thread.start()

        self.get_logger().info(f"Serial bridge node started on {port} at {baud} baud")
        self.odom_transform = TransformStamped()
        self.odom_transform.header.frame_id = "odom"
        self.odom_transform.child_frame_id = "base_footprint"
        self.odom_transform.transform.translation.x = 0.0
        self.odom_transform.transform.translation.y = 0.0
        self.odom_transform.transform.translation.z = 0.0
        self.odom_transform.transform.rotation = Quaternion()
        self.odom_transform.transform.rotation.x = 0.0
        self.odom_transform.transform.rotation.y = 0.0
        self.odom_transform.transform.rotation.z = 0.0
        self.odom_transform.transform.rotation.w = 1.0

    def connect_serial(self, port, baud, retries=5):
        for attempt in range(retries):
            try:
                self.get_logger().info(f"Connecting to {port}... (attempt {attempt+1}/{retries})")
                self.ser = serial.Serial(
                    port=port,
                    baudrate=baud,
                    timeout=1.0,
                    write_timeout=1.0,
                    exclusive=True,
                    dsrdtr=False,
                    rtscts=False
                )
                time.sleep(3)
                self.ser.reset_input_buffer()
                self.ser.reset_output_buffer()
                self.get_logger().info(f"Connected to {port}")
                return
            except serial.SerialException as e:
                self.get_logger().warn(f"Attempt {attempt+1}/{retries} failed: {e}")
                time.sleep(1)
        raise RuntimeError(f"Failed to connect to {port} after {retries} attempts")

    def cmd_vel_callback(self, msg):
        if not self.ser or not self.ser.is_open:
            self.get_logger().warn("Serial port not open, cannot send cmd_vel")
            return

        linear = msg.linear.x
        angular = msg.angular.z
        cmd = f"{linear:.2f} {angular:.2f}\n"

        try:
            with self.lock:
                self.ser.write(cmd.encode())
                self.ser.flush()
        except Exception as e:
            self.get_logger().error(f"Failed to write to serial: {e}")

    def read_serial(self):
        pos_re = re.compile(r'POS:\s*x\s*=\s*([-+]?\d+\.?\d*)\s+y\s*=\s*([-+]?\d+\.?\d*)\s+theta\s*=\s*([-+]?\d+\.?\d*)')

        consecutive_errors = 0
        max_consecutive_errors = 10

        while self.running and rclpy.ok():
            try:
                if not self.ser or not self.ser.is_open:
                    time.sleep(1)
                    continue

                if self.ser.in_waiting > 0:
                    with self.lock:
                        line = self.ser.readline().decode('utf-8', errors='ignore').strip()

                    if line:
                        self.lines_received += 1
                        match = pos_re.search(line)
                        if match:
                            try:
                                x, y, theta = map(float, match.groups())

                                self.odom_msg.header.stamp = self.get_clock().now().to_msg()
                                self.odom_msg.header.frame_id = "odom"
                                self.odom_msg.child_frame_id = "base_link"

                                # Use accumulated position
                                self.odom_msg.pose.pose.position.x = x
                                self.odom_msg.pose.pose.position.y = y
                                self.odom_msg.pose.pose.position.z = 0.0

                                q = self.yaw_to_quaternion(theta)
                                self.odom_msg.pose.pose.orientation = q

                                # Add twist (velocity) information
                                self.odom_msg.twist.twist.linear.x = 0.0  # Use delta as velocity
                                self.odom_msg.twist.twist.angular.z = 0.0  # Use delta as angular velocity

                                self.odom_msg.pose.covariance[0] = 0.01
                                self.odom_msg.pose.covariance[7] = 0.01
                                self.odom_msg.pose.covariance[35] = 0.01

                                self.odom_transform.header.stamp = self.odom_msg.header.stamp
                                self.odom_transform.transform.translation.x = x
                                self.odom_transform.transform.translation.y = y
                                self.odom_transform.transform.rotation = q

                                self.odom_pub.publish(self.odom_msg)
                                self.tf_broadcaster.sendTransform(self.odom_transform)

                                consecutive_errors = 0

                            except ValueError:
                                pass
                else:
                    time.sleep(0.001)
            except serial.SerialException as e:
                self.get_logger().error(f"Serial exception: {e}")
                consecutive_errors += 1
                if consecutive_errors >= max_consecutive_errors:
                    try:
                        if self.ser:
                            self.ser.close()
                        time.sleep(2)
                        self.connect_serial(
                            self.get_parameter('serial_port').value,
                            self.get_parameter('baud_rate').value
                        )
                        consecutive_errors = 0
                    except Exception as reconnect_error:
                        self.get_logger().error(f"Reconnect failed: {reconnect_error}")
                time.sleep(0.1)
            except Exception as e:
                import traceback
                self.get_logger().error(f"Unexpected error in read_serial: {e}")
                self.get_logger().error(traceback.format_exc())
                time.sleep(0.1)

    def yaw_to_quaternion(self, yaw):
        q = Quaternion()
        q.x = 0.0
        q.y = 0.0
        q.z = math.sin(yaw / 2.0)
        q.w = math.cos(yaw / 2.0)
        return q

    def send_restart(self):
        """Send a 'RESTART' command over serial right after connecting."""
        if not self.ser or not self.ser.is_open:
            self.get_logger().warn("Serial port not open, cannot send RESTART")
            return
        try:
            with self.lock:
                self.ser.write(b"RESTART\n")
                self.ser.flush()
            self.get_logger().info("Sent RESTART to serial device")
        except Exception as e:
            self.get_logger().error(f"Failed to write RESTART to serial: {e}")

    def destroy_node(self):
        self.get_logger().info("Shutting down...")
        self.running = False
        if self.thread.is_alive():
            self.thread.join(timeout=2.0)
        if self.ser and self.ser.is_open:
            self.ser.close()
        super().destroy_node()

def main(args=None):
    rclpy.init(args=args)
    node = None

    try:
        node = SerialBridgeNode()
        rclpy.spin(node)
    except KeyboardInterrupt:
        print("\nShutdown requested...")
    except Exception as e:
        if node:
            import traceback
            node.get_logger().error(f"Fatal error: {e}")
            node.get_logger().error(traceback.format_exc())
    finally:
        if node:
            node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
