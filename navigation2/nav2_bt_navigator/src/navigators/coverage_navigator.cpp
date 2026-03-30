#include <vector>
#include <string>
#include <memory>

#include "nav2_bt_navigator/navigators/coverage_navigator.hpp"
#include "nav2_util/geometry_utils.hpp"
#include "ament_index_cpp/get_package_share_directory.hpp"

namespace nav2_bt_navigator
{

bool
CoverageNavigator::configure(
  rclcpp_lifecycle::LifecycleNode::WeakPtr parent_node,
  std::shared_ptr<nav2_util::OdomSmoother> odom_smoother)
{
  start_time_ = rclcpp::Time(0);
  auto node = parent_node.lock();

  if (!node->has_parameter("coverage_goal_blackboard_id")) {
    node->declare_parameter("coverage_goal_blackboard_id", std::string("coverage_goal"));
  }
  goal_blackboard_id_ = node->get_parameter("coverage_goal_blackboard_id").as_string();

  if (!node->has_parameter("coverage_path_blackboard_id")) {
    node->declare_parameter("coverage_path_blackboard_id", std::string("coverage_path"));
  }
  path_blackboard_id_ = node->get_parameter("coverage_path_blackboard_id").as_string();

  odom_smoother_ = odom_smoother;

  return true;
}

std::string
CoverageNavigator::getDefaultBTFilepath(
  rclcpp_lifecycle::LifecycleNode::WeakPtr parent_node)
{
  std::string default_bt_xml_filename;
  auto node = parent_node.lock();

  if (!node->has_parameter("default_coverage_bt_xml")) {
    std::string pkg_share_dir =
      ament_index_cpp::get_package_share_directory("nav2_bt_navigator");

    node->declare_parameter<std::string>(
      "default_coverage_bt_xml",
      pkg_share_dir + "/behavior_trees/coverage_navigation.xml");
  }

  node->get_parameter("default_coverage_bt_xml", default_bt_xml_filename);
  return default_bt_xml_filename;
}

bool
CoverageNavigator::cleanup()
{
  return true;
}

bool
CoverageNavigator::goalReceived(ActionT::Goal::ConstSharedPtr goal)
{
  // ✅ behavior_tree removed from Goal → always use default BT
  auto bt_xml_filename = bt_action_server_->getDefaultBTFilename();

  if (!bt_action_server_->loadBehaviorTree(bt_xml_filename)) {
    RCLCPP_ERROR(
      logger_, "BT file not found: %s. Coverage planning canceled.",
      bt_xml_filename.c_str());
    return false;
  }

  start_time_ = clock_->now();

  auto blackboard = bt_action_server_->getBlackboard();
  blackboard->set<int>("number_recoveries", 0);  // NOLINT

  // Store coverage goal on blackboard
  blackboard->set<ActionT::Goal>(goal_blackboard_id_, *goal);

  RCLCPP_INFO(logger_, "Coverage planning goal received and set on blackboard");

  return true;
}

void
CoverageNavigator::goalCompleted(
  typename ActionT::Result::SharedPtr /*result*/,
  const nav2_behavior_tree::BtStatus /*final_bt_status*/)
{
}

void
CoverageNavigator::onLoop()
{
  // ✅ planning_time removed in new API → send empty feedback
  auto feedback_msg = std::make_shared<ActionT::Feedback>();
  bt_action_server_->publishFeedback(feedback_msg);
}

void
CoverageNavigator::onPreempt(ActionT::Goal::ConstSharedPtr /*goal*/)
{
  RCLCPP_INFO(logger_, "Received goal preemption request for coverage planning");

  // ✅ behavior_tree logic removed → always accept preemption
  goalReceived(bt_action_server_->acceptPendingGoal());
}

}  // namespace nav2_bt_navigator