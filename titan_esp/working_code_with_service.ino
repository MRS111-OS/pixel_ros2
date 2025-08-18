#include <micro_ros_arduino.h>
#include <Arduino.h>
#include <stdio.h>
#include <rcl/rcl.h>
#include <rcl/error_handling.h>
#include <rclc/rclc.h>
#include <rclc/executor.h>
#include <geometry_msgs/msg/twist.h>
#include <nav_msgs/msg/odometry.h>
#include <std_srvs/srv/set_bool.h>  // Add SetBool service header
#include <math.h>
#include <rosidl_runtime_c/string_functions.h>
#include "driver/gpio.h"

#define RCUTILS_LOG_MIN_SEVERITY RCUTILS_LOG_SEVERITY_NONE
#define RMW_UXRCE_ENTITY_CREATION_DESTROY_TIMEOUT 1000
#define RMW_UXRCE_PUBLISH_RELIABLE_TIMEOUT 1000

#define LED_PIN     2
#define PWM1        4    // OUT
#define IN1         16   // OUT
#define IN2         17   // OUT
#define PWM2        5    // OUT
#define INB1        18   // OUT
#define INB2        21   // OUT

// Buzzer pin definition - using a PWM-capable GPIO
#define BUZZER_PIN  14   // PWM-capable GPIO pin for buzzer
#define BUZZER_CHANNEL 2 // PWM channel for buzzer

// Encoder pins
#define M1_ENC_A    34   // Input-only
#define M1_ENC_B    35   // Input-only (or try 32, 33, 36, 39 if your board exposes them)
#define M2_ENC_A    13
#define M2_ENC_B    15

#define PWM_FREQ      10000
#define PWM_RES_BITS  8
#define DUTY_MAX      255
#define WHEEL_RADIUS  0.0325
#define BASE_WIDTH    0.18
#define TICKS_PER_REV 1000
#define ODOM_PERIOD_MS 100
#define PI 3.14159265f

// Buzzer frequency for tone generation
#define BUZZER_FREQ   1000  // 1kHz tone

float kp = 0.3, ki = 0.0, kd = 0.0;
volatile long m1_ticks = 0;
volatile long m2_ticks = 0;
volatile uint8_t last_m1_enc = 0, last_m2_enc = 0;
float target_l = 0, target_r = 0;
float pwm_l_cmd = 0, pwm_r_cmd = 0;
float integral_l = 0, integral_r = 0;
float error_l_prev = 0, error_r_prev = 0;
unsigned long last_time = 0, last_heartbeat = 0;
float x = 0, y = 0, theta = 0;
bool micro_ros_ok = false, ros_initialized = false;

rcl_publisher_t odom_publisher;
rcl_subscription_t cmd_vel_subscriber;
rcl_service_t buzzer_service;  // Add buzzer service
geometry_msgs__msg__Twist cmd_vel_msg;
nav_msgs__msg__Odometry odom_msg;
std_srvs__srv__SetBool_Request buzzer_req;   // Add buzzer service request
std_srvs__srv__SetBool_Response buzzer_res;  // Add buzzer service response
rclc_executor_t executor;
rclc_support_t support;
rcl_allocator_t allocator;
rcl_node_t node;
rcl_timer_t odom_timer;

#define RCCHECK(fn) {\
  rcl_ret_t _rc = fn;\
  if (_rc != RCL_RET_OK) {\
    Serial.printf("Error: %s failed, code %d\n", #fn, _rc);\
    micro_ros_ok = false;\
    return;\
  }\
}

#define RCSOFTCHECK(fn) {\
  rcl_ret_t _rc = fn;\
  if (_rc != RCL_RET_OK) {\
    Serial.printf("Soft error: %s, code %d\n", #fn, _rc);\
  }\
}

void IRAM_ATTR updateEnc1() {
  uint8_t MSB = gpio_get_level((gpio_num_t)M1_ENC_A);
  uint8_t LSB = gpio_get_level((gpio_num_t)M1_ENC_B);
  uint8_t enc = (MSB << 1) | LSB;
  uint8_t sum = (last_m1_enc << 2) | enc;
  if (sum == 0b0001 || sum == 0b0111 || sum == 0b1110 || sum == 0b1000) m1_ticks++;
  else if (sum == 0b0010 || sum == 0b1011 || sum == 0b1101 || sum == 0b0100) m1_ticks--;
  last_m1_enc = enc;
}

void IRAM_ATTR updateEnc2() {
  uint8_t MSB = gpio_get_level((gpio_num_t)M2_ENC_A);
  uint8_t LSB = gpio_get_level((gpio_num_t)M2_ENC_B);
  uint8_t enc = (MSB << 1) | LSB;
  uint8_t sum = (last_m2_enc << 2) | enc;
  if (sum == 0b0001 || sum == 0b0111 || sum == 0b1110 || sum == 0b1000) m2_ticks++;
  else if (sum == 0b0010 || sum == 0b1011 || sum == 0b1101 || sum == 0b0100) m2_ticks--;
  last_m2_enc = enc;
}

void driveMotorA(float pwm) {
  bool forward = (pwm >= 0);
  digitalWrite(IN1, forward ? HIGH : LOW);
  digitalWrite(IN2, forward ? LOW : HIGH);
  ledcWrite(PWM1, abs((int)pwm));
}

void driveMotorB(float pwm) {
  bool forward = (pwm >= 0);
  digitalWrite(INB1, forward ? HIGH : LOW);
  digitalWrite(INB2, forward ? LOW : HIGH);
  ledcWrite(PWM2, abs((int)pwm));
}

// Buzzer control functions
void buzzer_on() {
  ledcWriteTone(BUZZER_CHANNEL, BUZZER_FREQ);
  Serial.println("Buzzer ON");
}

void buzzer_off() {
  ledcWriteTone(BUZZER_CHANNEL, 0);
  Serial.println("Buzzer OFF");
}

// Buzzer service callback
void buzzer_service_callback(const void* req, void* res) {
  if (!micro_ros_ok) {
    Serial.println("buzzer_service_callback: micro_ros not ok, returning");
    return;
  }
  
  const auto* request = (const std_srvs__srv__SetBool_Request*)req;
  auto* response = (std_srvs__srv__SetBool_Response*)res;
  
  Serial.printf("Buzzer service called with data: %s\n", request->data ? "true" : "false");
  
  if (request->data) {
    buzzer_on();
    response->success = true;
    rosidl_runtime_c__String__assign(&response->message, "Buzzer turned ON");
  } else {
    buzzer_off();
    response->success = true;
    rosidl_runtime_c__String__assign(&response->message, "Buzzer turned OFF");
  }
}

void cmd_vel_callback(const void* msgin) {
  if (!micro_ros_ok) {
    Serial.println("cmd_vel_callback: micro_ros not ok, returning");
    return;
  }
  const auto* msg = (const geometry_msgs__msg__Twist*)msgin;
  float linear = msg->linear.x, angular = msg->angular.z;
  target_l = linear - (angular * BASE_WIDTH * 0.5f);
  target_r = linear + (angular * BASE_WIDTH * 0.5f);
  last_heartbeat = millis();
  Serial.printf("cmd_vel_callback: linear=%.3f angular=%.3f target_l=%.3f target_r=%.3f\n", linear, angular, target_l, target_r);
}

void odom_callback(rcl_timer_t*, int64_t) {
  if (!micro_ros_ok) {
    Serial.println("odom_callback: micro_ros not ok, returning");
    return;
  }
  unsigned long now = millis();
  float dt_s = (now - last_time) * 0.001f;
  if (dt_s <= 0.04f) {
    Serial.printf("odom_callback: dt_s too small (%.4f), skipping\n", dt_s);
    return;
  }
  if (now - last_heartbeat > 2000) {
    target_l = target_r = 0;
    pwm_l_cmd = pwm_r_cmd = 0;
    Serial.println("odom_callback: heartbeat timeout, motors stopped");
  }
  noInterrupts();
  long ticks_l = m1_ticks, ticks_r = m2_ticks;
  m1_ticks = m2_ticks = 0;
  interrupts();
  Serial.printf("odom_callback: ticks_l=%ld ticks_r=%ld\n", ticks_l, ticks_r);
  float w_l = (2 * PI * ticks_l / TICKS_PER_REV) / dt_s;
  float w_r = (2 * PI * ticks_r / TICKS_PER_REV) / dt_s;
  float v_l = w_l * WHEEL_RADIUS, v_r = w_r * WHEEL_RADIUS;
  float error_l = target_l - v_l;
  integral_l = constrain(integral_l + error_l * dt_s, -100.0f, 100.0f);
  float derivative_l = (error_l - error_l_prev) / dt_s;
  float correction_l = kp * error_l + ki * integral_l + kd * derivative_l;
  error_l_prev = error_l;
  pwm_l_cmd = constrain(pwm_l_cmd + correction_l * DUTY_MAX, -DUTY_MAX, DUTY_MAX);
  float error_r = target_r - v_r;
  integral_r = constrain(integral_r + error_r * dt_s, -100.0f, 100.0f);
  float derivative_r = (error_r - error_r_prev) / dt_s;
  float correction_r = kp * error_r + ki * integral_r + kd * derivative_r;
  error_r_prev = error_r;
  pwm_r_cmd = constrain(pwm_r_cmd + correction_r * DUTY_MAX, -DUTY_MAX, DUTY_MAX);
  Serial.printf("odom_callback: PWM cmds pwm_l=%.1f pwm_r=%.1f\n", pwm_l_cmd, pwm_r_cmd);
  driveMotorA(pwm_l_cmd);
  driveMotorB(pwm_r_cmd);
  float v = (v_r + v_l) * 0.5f;
  float w = (v_r - v_l) / BASE_WIDTH;
  x += v * cos(theta) * dt_s;
  y += v * sin(theta) * dt_s;
  theta += w * dt_s;
  while (theta > PI) theta -= 2 * PI;
  while (theta < -PI) theta += 2 * PI;
  odom_msg.header.stamp.sec = now / 1000;
  odom_msg.header.stamp.nanosec = (now % 1000) * 1000000;
  odom_msg.pose.pose.position.x = x;
  odom_msg.pose.pose.position.y = y;
  odom_msg.pose.pose.position.z = 0;
  odom_msg.pose.pose.orientation.x = 0;
  odom_msg.pose.pose.orientation.y = 0;
  odom_msg.pose.pose.orientation.z = sin(theta * 0.5f);
  odom_msg.pose.pose.orientation.w = cos(theta * 0.5f);
  odom_msg.twist.twist.linear.x = v;
  odom_msg.twist.twist.linear.y = 0;
  odom_msg.twist.twist.linear.z = 0;
  odom_msg.twist.twist.angular.x = 0;
  odom_msg.twist.twist.angular.y = 0;
  odom_msg.twist.twist.angular.z = w;
  rcl_ret_t ret = rcl_publish(&odom_publisher, &odom_msg, NULL);
  if (ret != RCL_RET_OK) {
    Serial.printf("Failed to publish odom: %d\n", ret);
  } else {
    Serial.println("odom published successfully");
  }
  last_time = now;
}

bool init_micro_ros() {
  Serial.println("init_micro_ros: Starting...");
  if (ros_initialized) {
    Serial.println("init_micro_ros: Cleaning up previous ROS resources...");
    rclc_executor_fini(&executor);
    rcl_timer_fini(&odom_timer);
    rcl_subscription_fini(&cmd_vel_subscriber, &node);
    rcl_publisher_fini(&odom_publisher, &node);
    rcl_service_fini(&buzzer_service, &node);  // Clean up buzzer service
    rcl_node_fini(&node);
    rclc_support_fini(&support);
    ros_initialized = false;
  }
  Serial.println("init_micro_ros: Setting transports...");
  set_microros_transports();
  delay(1000);
  allocator = rcl_get_default_allocator();
  if (rclc_support_init(&support, 0, NULL, &allocator) != RCL_RET_OK) {
    Serial.println("init_micro_ros: Failed to initialize support");
    return false;
  }
  Serial.println("init_micro_ros: Support initialized");
  if (rclc_node_init_default(&node, "diff_drive", "", &support) != RCL_RET_OK) {
    Serial.println("init_micro_ros: Failed to initialize node");
    return false;
  }
  Serial.println("init_micro_ros: Node initialized");
  if (rclc_publisher_init_default(&odom_publisher, &node, ROSIDL_GET_MSG_TYPE_SUPPORT(nav_msgs, msg, Odometry), "odom") != RCL_RET_OK) {
    Serial.println("init_micro_ros: Failed to initialize publisher");
    return false;
  }
  Serial.println("init_micro_ros: Publisher initialized");
  if (rclc_subscription_init_default(&cmd_vel_subscriber, &node, ROSIDL_GET_MSG_TYPE_SUPPORT(geometry_msgs, msg, Twist), "cmd_vel") != RCL_RET_OK) {
    Serial.println("init_micro_ros: Failed to initialize subscription");
    return false;
  }
  Serial.println("init_micro_ros: Subscription initialized");
  
  // Initialize buzzer service
  if (rclc_service_init_default(&buzzer_service, &node, ROSIDL_GET_SRV_TYPE_SUPPORT(std_srvs, srv, SetBool), "buzzer_control") != RCL_RET_OK) {
    Serial.println("init_micro_ros: Failed to initialize buzzer service");
    return false;
  }
  Serial.println("init_micro_ros: Buzzer service initialized");
  
  if (rclc_timer_init_default(&odom_timer, &support, RCL_MS_TO_NS(ODOM_PERIOD_MS), odom_callback) != RCL_RET_OK) {
    Serial.println("init_micro_ros: Failed to initialize timer");
    return false;
  }
  Serial.println("init_micro_ros: Timer initialized");
  
  // Initialize executor with 3 handles (timer, subscription, service)
  if (rclc_executor_init(&executor, &support.context, 3, &allocator) != RCL_RET_OK) {
    Serial.println("init_micro_ros: Failed to initialize executor");
    return false;
  }
  Serial.println("init_micro_ros: Executor initialized");
  rclc_executor_add_timer(&executor, &odom_timer);
  rclc_executor_add_subscription(&executor, &cmd_vel_subscriber, &cmd_vel_msg, &cmd_vel_callback, ON_NEW_DATA);
  rclc_executor_add_service(&executor, &buzzer_service, &buzzer_req, &buzzer_res, buzzer_service_callback);  // Add buzzer service to executor
  
  rosidl_runtime_c__String__init(&odom_msg.header.frame_id);
  rosidl_runtime_c__String__assign(&odom_msg.header.frame_id, "odom");
  rosidl_runtime_c__String__init(&odom_msg.child_frame_id);
  rosidl_runtime_c__String__assign(&odom_msg.child_frame_id, "base_link");
  
  // Initialize buzzer service response message
  rosidl_runtime_c__String__init(&buzzer_res.message);
  
  ros_initialized = true;
  Serial.println("init_micro_ros: Initialization complete");
  return true;
}

void setup() {
  Serial.begin(115200);
  while (!Serial && millis() < 5000) delay(10);
  Serial.println("Setup: Serial started");
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, HIGH);
  Serial.println("Setup: LED pin configured HIGH");
  Serial.println("Setup: Initial heap:");
  Serial.printf("  %d bytes\n", ESP.getFreeHeap());
  
  // Motor pins
  Serial.println("Setup: Configuring motor pins...");
  pinMode(IN1, OUTPUT);
  pinMode(IN2, OUTPUT);
  pinMode(INB1, OUTPUT);
  pinMode(INB2, OUTPUT);
  digitalWrite(IN1, LOW);
  digitalWrite(IN2, LOW);
  digitalWrite(INB1, LOW);
  digitalWrite(INB2, LOW);
  Serial.println("Setup: Motor pins configured LOW");
  Serial.println("Setup: Attaching PWM pins...");
  if (!ledcAttach(PWM1, PWM_FREQ, PWM_RES_BITS)) {
    Serial.println("ERROR: Failed to attach PWM1!");
    while(1) { digitalWrite(LED_PIN, !digitalRead(LED_PIN)); delay(500); }
  }
  if (!ledcAttach(PWM2, PWM_FREQ, PWM_RES_BITS)) {
    Serial.println("ERROR: Failed to attach PWM2!");
    while(1) { digitalWrite(LED_PIN, !digitalRead(LED_PIN)); delay(500); }
  }
  Serial.println("Setup: PWM pins attached");
  ledcWrite(PWM1, 0);
  ledcWrite(PWM2, 0);
  Serial.println("Setup: PWM output set to 0");
  
  // Buzzer setup
  Serial.println("Setup: Configuring buzzer...");
  if (!ledcAttach(BUZZER_PIN, BUZZER_FREQ, PWM_RES_BITS)) {
    Serial.println("ERROR: Failed to attach buzzer PWM!");
    while(1) { digitalWrite(LED_PIN, !digitalRead(LED_PIN)); delay(500); }
  }
  ledcWrite(BUZZER_CHANNEL, 0);  // Start with buzzer off
  Serial.println("Setup: Buzzer configured and turned off");
  
  // Encoders
  Serial.println("Setup: Configuring encoder pins...");
  pinMode(M1_ENC_A, INPUT_PULLUP); Serial.println("M1_ENC_A OK");
  pinMode(M1_ENC_B, INPUT_PULLUP); Serial.println("M1_ENC_B OK");
  pinMode(M2_ENC_A, INPUT_PULLUP); Serial.println("M2_ENC_A OK");
  pinMode(M2_ENC_B, INPUT_PULLUP); Serial.println("M2_ENC_B OK");
  delay(50);
  Serial.println("All encoder pins configured.");
  last_m1_enc = (gpio_get_level((gpio_num_t)M1_ENC_A) << 1) | gpio_get_level((gpio_num_t)M1_ENC_B);
  last_m2_enc = (gpio_get_level((gpio_num_t)M2_ENC_A) << 1) | gpio_get_level((gpio_num_t)M2_ENC_B);
  attachInterrupt(digitalPinToInterrupt(M1_ENC_A), updateEnc1, CHANGE);
  attachInterrupt(digitalPinToInterrupt(M1_ENC_B), updateEnc1, CHANGE);
  attachInterrupt(digitalPinToInterrupt(M2_ENC_A), updateEnc2, CHANGE);
  attachInterrupt(digitalPinToInterrupt(M2_ENC_B), updateEnc2, CHANGE);
  Serial.println("Setup: Encoder interrupts attached");
  last_time = last_heartbeat = millis();
  micro_ros_ok = init_micro_ros();
  Serial.printf("Setup: micro-ROS initialization %s\n", micro_ros_ok ? "succeeded" : "failed");
  Serial.printf("Setup: Heap after setup: %d bytes\n", ESP.getFreeHeap());
  digitalWrite(LED_PIN, micro_ros_ok ? LOW : HIGH);
  Serial.println("Setup complete\n");
}

void loop() {
  unsigned long now = millis();
  if (micro_ros_ok) {
    rcl_ret_t ret = rclc_executor_spin_some(&executor, RCL_MS_TO_NS(10));
    if (ret != RCL_RET_OK && ret != RCL_RET_TIMEOUT) {
      Serial.printf("Executor error: %d\n", ret);
      micro_ros_ok = false;
    }
  } else if ((now - last_time) > 5000) {
    Serial.println("Loop: micro-ROS not ok, retrying initialization...");
    micro_ros_ok = init_micro_ros();
    last_time = now;
  }
  // Blink LED quickly every second for heartbeat
  digitalWrite(LED_PIN, (now % 1000) < 100 ? LOW : HIGH);
  yield();
  delay(1);
}
