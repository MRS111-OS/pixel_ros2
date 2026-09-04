#include <rclcpp/rclcpp.hpp>

#include <nav_msgs/msg/path.hpp>
#include <nav_msgs/msg/occupancy_grid.hpp>

#include <cmath>
#include <limits>
#include <vector>

class PlannerMetricsNode : public rclcpp::Node
{
public:
  PlannerMetricsNode()
  : Node("planner_metrics_node")
  {
    plan_sub_ = this->create_subscription<nav_msgs::msg::Path>(
      "/plan",
      rclcpp::QoS(10),
      std::bind(&PlannerMetricsNode::onPlan, this, std::placeholders::_1));

    costmap_sub_ = this->create_subscription<nav_msgs::msg::OccupancyGrid>(
      "/global_costmap/costmap",
      rclcpp::QoS(1),
      std::bind(&PlannerMetricsNode::onCostmap, this, std::placeholders::_1));

    RCLCPP_INFO(this->get_logger(),
      "Planner metrics node started.\n"
      "Listening to /plan and /global_costmap/costmap");
  }

private:
  rclcpp::Subscription<nav_msgs::msg::Path>::SharedPtr plan_sub_;
  rclcpp::Subscription<nav_msgs::msg::OccupancyGrid>::SharedPtr costmap_sub_;

  nav_msgs::msg::OccupancyGrid::SharedPtr latest_costmap_;

  /* ============================
     Costmap callback
     ============================ */
  void onCostmap(const nav_msgs::msg::OccupancyGrid::SharedPtr msg)
  {
    latest_costmap_ = msg;
  }

  /* ============================
     Plan callback
     ============================ */
  void onPlan(const nav_msgs::msg::Path::SharedPtr path)
  {
    const size_t n = path->poses.size();

    if (n < 2) {
      RCLCPP_WARN(this->get_logger(),
        "Received plan with < 2 poses, skipping metrics.");
      return;
    }

    const double length = computePathLength(path);
    const double smoothness = computeSmoothness(path);
    const double clearance =
      latest_costmap_ ? computeClearance(path) : -1.0;

    RCLCPP_INFO(this->get_logger(),
      "\n================ PLANNER METRICS ================\n"
      "Path points   : %zu\n"
      "Path length   : %.3f m\n"
      "Smoothness    : %.3f rad\n"
      "Min clearance : %.3f m\n"
      "=================================================\n",
      n, length, smoothness, clearance);
  }

  /* ============================
     Metric computations
     ============================ */

  double computePathLength(const nav_msgs::msg::Path::SharedPtr path)
  {
    double length = 0.0;

    for (size_t i = 1; i < path->poses.size(); ++i) {
      const auto & a = path->poses[i - 1].pose.position;
      const auto & b = path->poses[i].pose.position;
      length += std::hypot(b.x - a.x, b.y - a.y);
    }

    return length;
  }

  double computeSmoothness(const nav_msgs::msg::Path::SharedPtr path)
  {
    if (path->poses.size() < 3) {
      return 0.0;
    }

    double smoothness = 0.0;
    double prev_heading = 0.0;
    bool first = true;

    for (size_t i = 1; i < path->poses.size(); ++i) {
      const auto & a = path->poses[i - 1].pose.position;
      const auto & b = path->poses[i].pose.position;

      const double heading = std::atan2(b.y - a.y, b.x - a.x);

      if (!first) {
        smoothness += std::fabs(heading - prev_heading);
      } else {
        first = false;
      }

      prev_heading = heading;
    }

    return smoothness;
  }

  double computeClearance(const nav_msgs::msg::Path::SharedPtr path)
  {
    const auto & info = latest_costmap_->info;
    double min_clearance = std::numeric_limits<double>::max();

    for (const auto & pose : path->poses) {
      const double wx = pose.pose.position.x;
      const double wy = pose.pose.position.y;

      const int mx =
        static_cast<int>((wx - info.origin.position.x) / info.resolution);
      const int my =
        static_cast<int>((wy - info.origin.position.y) / info.resolution);

      if (mx < 0 || my < 0 ||
          mx >= static_cast<int>(info.width) ||
          my >= static_cast<int>(info.height)) {
        continue;
      }

      const int index = my * info.width + mx;
      const int cost = latest_costmap_->data[index];

      if (cost >= 0) {
        const double clearance = (100 - cost) * info.resolution;
        min_clearance = std::min(min_clearance, clearance);
      }
    }

    if (min_clearance == std::numeric_limits<double>::max()) {
      return -1.0;
    }

    return min_clearance;
  }
};


int main(int argc, char ** argv)
{
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<PlannerMetricsNode>());
  rclcpp::shutdown();
  return 0;
}
