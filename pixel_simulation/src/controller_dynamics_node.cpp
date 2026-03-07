#include <rclcpp/rclcpp.hpp>
#include <geometry_msgs/msg/twist.hpp>

class ControllerDynamicsNode : public rclcpp::Node
{
public:
  ControllerDynamicsNode()
  : Node("controller_dynamics_node"),
    first_msg_(true)
  {
    cmd_vel_sub_ = this->create_subscription<geometry_msgs::msg::Twist>(
      "/cmd_vel",
      rclcpp::QoS(50),
      std::bind(&ControllerDynamicsNode::onCmdVel, this, std::placeholders::_1));

    start_time_ = this->now();

    RCLCPP_INFO(this->get_logger(),
      "Controller dynamics node started.\n"
      "Listening to /cmd_vel");
  }

private:
  rclcpp::Subscription<geometry_msgs::msg::Twist>::SharedPtr cmd_vel_sub_;

  double last_linear_vel_;
  double last_angular_vel_;
  rclcpp::Time last_time_;
  rclcpp::Time start_time_;
  bool first_msg_;

  void onCmdVel(const geometry_msgs::msg::Twist::SharedPtr msg)
  {
    const rclcpp::Time now = this->now();

    if (first_msg_) {
      last_linear_vel_ = msg->linear.x;
      last_angular_vel_ = msg->angular.z;
      last_time_ = now;
      first_msg_ = false;
      return;
    }

    const double dt = (now - last_time_).seconds();
    if (dt <= 0.0) {
      return;
    }

    const double v = msg->linear.x;
    const double w = msg->angular.z;

    const double linear_acc = (v - last_linear_vel_) / dt;
    const double angular_acc = (w - last_angular_vel_) / dt;

    const double t = (now - start_time_).seconds();

    RCLCPP_INFO(
      this->get_logger(),
      "t=%.3f  v=%.3f m/s  w=%.3f rad/s  dv/dt=%.3f m/s^2  dw/dt=%.3f rad/s^2",
      t, v, w, linear_acc, angular_acc
    );

    last_linear_vel_ = v;
    last_angular_vel_ = w;
    last_time_ = now;
  }
};

int main(int argc, char ** argv)
{
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<ControllerDynamicsNode>());
  rclcpp::shutdown();
  return 0;
}
