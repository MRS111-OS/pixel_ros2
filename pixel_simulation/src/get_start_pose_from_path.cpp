#include "behaviortree_cpp_v3/action_node.h"
#include "nav_msgs/msg/path.hpp"
#include "geometry_msgs/msg/pose_stamped.hpp"

class GetStartPoseFromPath : public BT::SyncActionNode
{
public:
  GetStartPoseFromPath(
    const std::string & name,
    const BT::NodeConfiguration & config)
  : BT::SyncActionNode(name, config) {}

  static BT::PortsList providedPorts()
  {
    return {
      BT::InputPort<nav_msgs::msg::Path>("path"),
      BT::OutputPort<geometry_msgs::msg::PoseStamped>("start_pose")
    };
  }

  BT::NodeStatus tick() override
  {
    nav_msgs::msg::Path path;

    // Get input
    if (!getInput("path", path)) {
      throw BT::RuntimeError("Missing required input [path]");
    }

    if (path.poses.empty()) {
      throw BT::RuntimeError("Path is empty!");
    }

    // Extract first pose
    auto start_pose = path.poses.front();

    // Set output
    setOutput("start_pose", start_pose);

    return BT::NodeStatus::SUCCESS;
  }
};

#include "behaviortree_cpp_v3/bt_factory.h"

BT_REGISTER_NODES(factory)
{
  factory.registerNodeType<GetStartPoseFromPath>("GetStartPoseFromPath");
}