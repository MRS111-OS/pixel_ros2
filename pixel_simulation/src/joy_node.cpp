#include <rclcpp/rclcpp.hpp>
#include <sensor_msgs/msg/joy.hpp>

#include <termios.h>
#include <unistd.h>
#include <fcntl.h>
#include <string>
#include <sstream>
#include <cmath>

class JoyNode : public rclcpp::Node
{
public:
  JoyNode() : Node("joy_node")
  {
    joy_pub_ = this->create_publisher<sensor_msgs::msg::Joy>("/joy", 10);

    open_serial("/dev/ttyACM0");

    timer_ = this->create_wall_timer(
      std::chrono::milliseconds(20),
      std::bind(&JoyNode::read_serial, this));

    RCLCPP_INFO(this->get_logger(), "joy_node started");
  }

private:
  int serial_fd_{-1};
  std::string serial_buffer_;

  rclcpp::Publisher<sensor_msgs::msg::Joy>::SharedPtr joy_pub_;
  rclcpp::TimerBase::SharedPtr timer_;

  // --- filtering ---
  float center_lx_ = 128.0f;
  float center_ly_ = 128.0f;
  float center_rx_ = 128.0f;
  float center_ry_ = 128.0f;

  const float CENTER_ALPHA = 0.002f;   // slow drift compensation
  const float DEADZONE = 0.05f;

  void open_serial(const std::string &port)
  {
    serial_fd_ = open(port.c_str(), O_RDONLY | O_NOCTTY | O_NONBLOCK);
    if (serial_fd_ < 0) {
      RCLCPP_FATAL(this->get_logger(), "Failed to open %s", port.c_str());
      rclcpp::shutdown();
      return;
    }

    termios tty{};
    tcgetattr(serial_fd_, &tty);

    cfsetispeed(&tty, B115200);
    cfsetospeed(&tty, B115200);

    tty.c_cflag |= (CLOCAL | CREAD);
    tty.c_cflag &= ~CSIZE;
    tty.c_cflag |= CS8;
    tty.c_cflag &= ~PARENB;
    tty.c_cflag &= ~CSTOPB;
    tty.c_cflag &= ~CRTSCTS;

    tty.c_lflag = 0;
    tty.c_oflag = 0;
    tty.c_iflag = 0;

    tcsetattr(serial_fd_, TCSANOW, &tty);
  }

  int extract(const std::string &line, const std::string &key)
  {
    auto pos = line.find(key + ":");
    if (pos == std::string::npos)
      return -1;

    pos += key.length() + 1;
    std::stringstream ss(line.substr(pos));
    int v;
    ss >> v;
    return v;
  }

  float process_axis(int raw, float &center)
  {
    // slowly track center ONLY when near it
    if (std::abs(raw - center) < 5.0f)
      center = (1.0f - CENTER_ALPHA) * center + CENTER_ALPHA * raw;

    float v = (raw - center) / 128.0f;

    if (std::fabs(v) < DEADZONE)
      return 0.0f;

    return std::max(-1.0f, std::min(1.0f, v));
  }

  void read_serial()
  {
    char buf[128];
    int n = read(serial_fd_, buf, sizeof(buf));
    if (n <= 0)
      return;

    serial_buffer_.append(buf, n);

    size_t pos;
    while ((pos = serial_buffer_.find('\n')) != std::string::npos)
    {
      std::string line = serial_buffer_.substr(0, pos);
      serial_buffer_.erase(0, pos + 1);
      process_line(line);
    }
  }

  void process_line(const std::string &line)
  {
    int lx = extract(line, "LX");
    int ly = extract(line, "LY");
    int rx = extract(line, "RX");
    int ry = extract(line, "RY");
    int x  = extract(line, "X");
    int o  = extract(line, "O");

    if (lx < 0 || ly < 0 || rx < 0 || ry < 0)
      return;

    sensor_msgs::msg::Joy joy;
    joy.axes.resize(6, 0.0f);
    joy.buttons.resize(8, 0);

    joy.axes[0] = process_axis(lx, center_lx_);
    joy.axes[1] = process_axis(ly, center_ly_);   // linear.x
    joy.axes[2] = process_axis(rx, center_rx_);   // angular.z
    joy.axes[3] = process_axis(ry, center_ry_);

    joy.buttons[0] = (x > 0);
    joy.buttons[2] = (o > 0);   // enable button

    joy_pub_->publish(joy);
  }
};

int main(int argc, char **argv)
{
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<JoyNode>());
  rclcpp::shutdown();
  return 0;
}
