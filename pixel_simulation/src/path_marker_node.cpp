#include <rclcpp/rclcpp.hpp>
#include <nav_msgs/msg/odometry.hpp>
#include <visualization_msgs/msg/marker.hpp>
#include <geometry_msgs/msg/point.hpp>

class PathMarkerNode : public rclcpp::Node
{
public:
  PathMarkerNode()
  : Node("path_marker_node")
  {
    // Publisher for RViz marker
    marker_pub_ = this->create_publisher<visualization_msgs::msg::Marker>(
      "/robot_path_marker", 10);

    // Subscribe to odometry
    odom_sub_ = this->create_subscription<nav_msgs::msg::Odometry>(
      "/odom", 10,
      std::bind(&PathMarkerNode::odomCallback, this, std::placeholders::_1));

    // Initialize marker
    marker_.header.frame_id = "map";   // IMPORTANT
    marker_.ns = "robot_path";
    marker_.id = 0;
    marker_.type = visualization_msgs::msg::Marker::LINE_STRIP;
    marker_.action = visualization_msgs::msg::Marker::ADD;

    // Line width
    marker_.scale.x = 0.05;

    // Color (red)
    marker_.color.r = 1.0;
    marker_.color.g = 0.0;
    marker_.color.b = 0.0;
    marker_.color.a = 1.0;

    marker_.pose.orientation.w = 1.0;

    RCLCPP_INFO(this->get_logger(), "Path marker node started");
  }

private:
  void odomCallback(const nav_msgs::msg::Odometry::SharedPtr msg)
  {
    marker_.header.stamp = this->get_clock()->now();

    geometry_msgs::msg::Point p;
    p.x = msg->pose.pose.position.x;
    p.y = msg->pose.pose.position.y;
    p.z = 0.05;  // slightly above ground

    marker_.points.push_back(p);

    marker_pub_->publish(marker_);
  }

  rclcpp::Publisher<visualization_msgs::msg::Marker>::SharedPtr marker_pub_;
  rclcpp::Subscription<nav_msgs::msg::Odometry>::SharedPtr odom_sub_;

  visualization_msgs::msg::Marker marker_;
};

int main(int argc, char **argv)
{
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<PathMarkerNode>());
  rclcpp::shutdown();
  return 0;
}
