#!/usr/bin/env python3
"""
Flips the incoming camera image by 180 degrees (both axes).
Used when the camera module is mounted upside-down and the hardware
dtoverlay vflip/hflip approach is not supported by the libcamera version.

Subscribes: image_in  (sensor_msgs/Image) — remapped to raw unflipped topic
Publishes:  image_out (sensor_msgs/Image) — remapped to /camera/image_raw
"""

import cv2
import rclpy
from cv_bridge import CvBridge
from rclpy.node import Node
from rclpy.qos import QoSHistoryPolicy, QoSProfile, QoSReliabilityPolicy
from sensor_msgs.msg import Image


class FlipImageNode(Node):

    def __init__(self):
        super().__init__('flip_image')

        self.bridge = CvBridge()

        # Subscriber QoS: Best Effort + depth=1 accepts both Reliable and Best Effort camera feeds
        sub_qos = QoSProfile(
            reliability=QoSReliabilityPolicy.BEST_EFFORT,
            history=QoSHistoryPolicy.KEEP_LAST,
            depth=1,
        )

        # Publisher QoS: Reliable + depth=1 ensures RViz and downstream nodes (republish)
        # can connect regardless of whether they expect Reliable or Best Effort, while depth=1 prevents buffering
        pub_qos = QoSProfile(
            reliability=QoSReliabilityPolicy.RELIABLE,
            history=QoSHistoryPolicy.KEEP_LAST,
            depth=1,
        )

        self.sub = self.create_subscription(Image, 'image_in',  self.callback, sub_qos)
        self.pub = self.create_publisher(Image,    'image_out', pub_qos)

        self.declare_parameter('flip_mode', -1)
        self.flip_mode = int(self.get_parameter('flip_mode').value)

        self.get_logger().info(
            f'FlipImageNode started — flip_mode={self.flip_mode} (-1: 180° rotation, 0: vertical, 1: horizontal)'
        )

    def callback(self, msg: Image) -> None:
        try:
            self.get_logger().info('Received camera frame, flipping and publishing...', once=True)

            # Convert ROS Image → OpenCV
            img = self.bridge.imgmsg_to_cv2(msg, desired_encoding='passthrough')

            # Flip according to flip_mode (-1 = 180° both axes)
            flipped = cv2.flip(img, self.flip_mode)

            # Convert back to ROS Image and preserve the original header
            out_msg = self.bridge.cv2_to_imgmsg(flipped, encoding=msg.encoding)
            out_msg.header = msg.header

            self.pub.publish(out_msg)

        except Exception as e:  # noqa: BLE001
            self.get_logger().error(f'Failed to flip image: {e}')


def main(args=None) -> None:
    rclpy.init(args=args)
    node = FlipImageNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
