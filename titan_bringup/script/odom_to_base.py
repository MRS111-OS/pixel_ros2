#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry
from geometry_msgs.msg import TransformStamped
from tf2_ros import TransformBroadcaster


class OdomToTFBroadcaster(Node):
    """
    ROS2 node that subscribes to /odom topic and broadcasts
    the transform from odom to base_footprint frame.
    """
    
    def __init__(self):
        super().__init__('odom_to_tf_broadcaster')
        
        # Initialize the transform broadcaster
        self.tf_broadcaster = TransformBroadcaster(self)
        
        # Subscribe to the /odom topic
        self.odom_subscription = self.create_subscription(
            Odometry,
            '/odom',
            self.odom_callback,
            10
        )
        
        self.get_logger().info('Odom to TF broadcaster node started')
    
    def odom_callback(self, msg):
        """
        Callback function that receives Odometry messages and
        publishes the corresponding transform.
        
        Args:
            msg (Odometry): The odometry message from /odom topic
        """
        # Create a TransformStamped message
        t = TransformStamped()
        
        # Set the timestamp and frame IDs
        t.header.stamp = self.get_clock().now().to_msg()
        t.header.frame_id = msg.header.frame_id  # "odom"
        t.child_frame_id = msg.child_frame_id    # "base_footprint"
        
        # Extract position from odometry message
        t.transform.translation.x = msg.pose.pose.position.x
        t.transform.translation.y = msg.pose.pose.position.y
        t.transform.translation.z = msg.pose.pose.position.z
        
        # Extract orientation (quaternion) from odometry message
        t.transform.rotation.x = msg.pose.pose.orientation.x
        t.transform.rotation.y = msg.pose.pose.orientation.y
        t.transform.rotation.z = msg.pose.pose.orientation.z
        t.transform.rotation.w = msg.pose.pose.orientation.w
        
        # Broadcast the transform
        self.tf_broadcaster.sendTransform(t)


def main(args=None):
    # Initialize the ROS2 Python client library
    rclpy.init(args=args)
    
    # Create the node
    node = OdomToTFBroadcaster()
    
    try:
        # Spin the node to keep it alive and processing callbacks
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        # Clean shutdown
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
