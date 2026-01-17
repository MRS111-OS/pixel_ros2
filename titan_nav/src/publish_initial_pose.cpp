#include "rclcpp/rclcpp.hpp"
#include "geometry_msgs/msg/pose_with_covariance_stamped.hpp"

class InitialPosePublisher : public rclcpp::Node
{
public:
    InitialPosePublisher()
    : Node("initial_pose_publisher")
    {
        publisher_ = this->create_publisher<geometry_msgs::msg::PoseWithCovarianceStamped>("/initialpose", 10);

        // Timer to publish after a short delay
        timer_ = this->create_wall_timer(
            std::chrono::seconds(3),
            std::bind(&InitialPosePublisher::publish_pose, this)
        );

        RCLCPP_INFO(this->get_logger(), "InitialPosePublisher started...");
    }

private:
    void publish_pose()
    {
        geometry_msgs::msg::PoseWithCovarianceStamped msg;
        msg.header.frame_id = "map";
        msg.header.stamp = this->get_clock()->now();

        // --- Pose ---
        msg.pose.pose.position.x = 0.003;
        msg.pose.pose.position.y = -0.030;
        msg.pose.pose.position.z = 0.0;
        msg.pose.pose.orientation.z = 0.0035;
        msg.pose.pose.orientation.w = 0.99999;

        // --- Covariance (small uncertainty) ---
        msg.pose.covariance[0] = 0.25;
        msg.pose.covariance[7] = 0.25;
        msg.pose.covariance[35] = 0.0685;

        publisher_->publish(msg);
        RCLCPP_INFO(this->get_logger(), "✅ Published initial pose to /initialpose");

        published_ = true;
        timer_->cancel();  // only publish once
    }

    rclcpp::Publisher<geometry_msgs::msg::PoseWithCovarianceStamped>::SharedPtr publisher_;
    rclcpp::TimerBase::SharedPtr timer_;
    bool published_ = false;
};

int main(int argc, char **argv)
{
    rclcpp::init(argc, argv);
    rclcpp::spin(std::make_shared<InitialPosePublisher>());
    rclcpp::shutdown();
    return 0;
}
