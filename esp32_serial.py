import rclpy
from rclpy.node import Node
from std_msgs.msg import Int32
import serial

class SerialPubSub(Node):
    def __init__(self):
        super().__init__('serial_pub_sub_node')

        # Publisher
        self.publisher_ = self.create_publisher(Int32, 'esp32_data', 10)

        # Subscriber
        self.subscription = self.create_subscription(
            Int32,
            'esp32_data',
            self.listener_callback,
            10
        )

        # Serial Connection
        try:
            self.ser = serial.Serial('/dev/ttyUSB0', 115200, timeout=1)
            self.get_logger().info('Serial connected on /dev/ttyUSB0 at 115200 baud')
        except serial.SerialException as e:
            self.get_logger().error(f'Serial connection failed: {e}')
            self.ser = None

        # Timer to poll serial
        self.timer = self.create_timer(0.5, self.timer_callback)  # 2Hz

    def timer_callback(self):
        if self.ser and self.ser.in_waiting:
            line = self.ser.readline().decode('utf-8').strip()
            try:
                value = int(line)
                msg = Int32()
                msg.data = value
                self.publisher_.publish(msg)
                self.get_logger().info(f'Published: {value}')
            except ValueError:
                self.get_logger().warn(f'Non-integer received: "{line}"')

    def listener_callback(self, msg):
        self.get_logger().info(f'Received from topic: {msg.data}')

def main(args=None):
    rclpy.init(args=args)
    node = SerialPubSub()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
