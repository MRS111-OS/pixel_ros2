#include <Arduino.h>

#define PI 3.14159265f

// === Motor Pins ===
#define PWM1 4
#define IN1 16
#define IN2 17
#define PWM2 5
#define INB1 18
#define INB2 19

// === Encoder Pins ===
#define M1_ENC_A 27
#define M1_ENC_B 14
#define M2_ENC_A 26
#define M2_ENC_B 25

// === Constants ===
#define PWM_FREQ     10000
#define PWM_RES_BITS 8
#define DUTY_MAX     255

#define WHEEL_RADIUS 0.0325  // meters
#define BASE_WIDTH   0.18   // distance between wheels (meters)
#define TICKS_PER_REV 1000   // encoder resolution
#define GEAR_RATIO 1.0

// === PID parameters ===
float kp = 0.3, ki = 0.0, kd = 0.00;

// === State ===
volatile long m1_ticks = 0;
volatile long m2_ticks = 0;
volatile uint8_t last_m1_enc = 0;
volatile uint8_t last_m2_enc = 0;

float m1_speed = 0, m2_speed = 0;
float target_l = 0, target_r = 0;
float pwm_l_cmd = 0, pwm_r_cmd = 0;
float integral_l = 0, integral_r = 0;
float error_l_prev = 0, error_r_prev = 0;

unsigned long last_time = 0;

// === Odometry ===
float x = 0, y = 0, theta = 0;

void IRAM_ATTR updateEnc1() {
  uint8_t MSB = digitalRead(M1_ENC_A);
  uint8_t LSB = digitalRead(M1_ENC_B);
  uint8_t enc = (MSB << 1) | LSB;
  uint8_t sum = (last_m1_enc << 2) | enc;

  if (sum == 0b0001 || sum == 0b0111 || sum == 0b1110 || sum == 0b1000)
    m1_ticks++;
  else if (sum == 0b0010 || sum == 0b1011 || sum == 0b1101 || sum == 0b0100)
    m1_ticks--;

  last_m1_enc = enc;
}

void IRAM_ATTR updateEnc2() {
  uint8_t MSB = digitalRead(M2_ENC_A);
  uint8_t LSB = digitalRead(M2_ENC_B);
  uint8_t enc = (MSB << 1) | LSB;
  uint8_t sum = (last_m2_enc << 2) | enc;

  if (sum == 0b0001 || sum == 0b0111 || sum == 0b1110 || sum == 0b1000)
    m2_ticks++;
  else if (sum == 0b0010 || sum == 0b1011 || sum == 0b1101 || sum == 0b0100)
    m2_ticks--;

  last_m2_enc = enc;
}

void driveMotorA(float pwm) {
  bool forward = pwm >= 0;
  digitalWrite(IN1, forward ? HIGH : LOW);
  digitalWrite(IN2, forward ? LOW : HIGH);
  ledcWrite(PWM1, abs((int)pwm));
}

void driveMotorB(float pwm) {
  bool forward = pwm <= 0;
  digitalWrite(INB1, forward ? HIGH : LOW);
  digitalWrite(INB2, forward ? LOW : HIGH);
  ledcWrite(PWM2, abs((int)pwm));
}

void setup() {
  Serial.begin(115200);
  delay(1000);
  Serial.println("ESP32 Differential Drive with PID and Odometry");

  // Motor Pins
  pinMode(IN1, OUTPUT);
  pinMode(IN2, OUTPUT);
  pinMode(INB1, OUTPUT);
  pinMode(INB2, OUTPUT);

  ledcAttach(PWM1, PWM_FREQ, PWM_RES_BITS);
  ledcAttach(PWM2, PWM_FREQ, PWM_RES_BITS);
  ledcWrite(PWM1, 0);
  ledcWrite(PWM2, 0);

  // Encoder Pins
  pinMode(M1_ENC_A, INPUT_PULLUP);
  pinMode(M1_ENC_B, INPUT_PULLUP);
  pinMode(M2_ENC_A, INPUT_PULLUP);
  pinMode(M2_ENC_B, INPUT_PULLUP);

  attachInterrupt(digitalPinToInterrupt(M1_ENC_A), updateEnc1, CHANGE);
  attachInterrupt(digitalPinToInterrupt(M1_ENC_B), updateEnc1, CHANGE);
  attachInterrupt(digitalPinToInterrupt(M2_ENC_A), updateEnc2, CHANGE);
  attachInterrupt(digitalPinToInterrupt(M2_ENC_B), updateEnc2, CHANGE);

  last_time = millis();
}

void loop() {
  unsigned long now = millis();
  float dt = (now - last_time);
  if (dt < 40) return; // skip if too soon
//  Serial.printf("Loop dt : %0.2f \n", dt);/

  // Compute current speed (rad/s)
  long ticks_l = m1_ticks;
  long ticks_r = m2_ticks;
//  Serial.printf("Ticks L: %ld | Ticks R: %ld\n", m1_ticks, m2_ticks);/
  m1_ticks = m2_ticks = 0;

  float w_l = (2.0 * PI * (float)ticks_l / (float)TICKS_PER_REV) / (dt / 1000);
  float w_r = (2.0 * PI * (float)ticks_r / (float)TICKS_PER_REV) / (dt / 1000);
//  float w_r = (2 * PI * ticks_r / TICKS_PER_REV) // dt;

  float v_l = w_l * WHEEL_RADIUS;
  float v_r = w_r * WHEEL_RADIUS;

//  Serial.printf("w_l: %.4f rad/s | w_r: %.4f rad/s | v_l: %.4f m/s | v_r: %.4/f m/s\n", w_l, w_r, v_l, v_r);


  // === PID Control ===
  float error_l = target_l - v_l;
  integral_l += error_l * dt;
  float derivative_l = (error_l - error_l_prev) / dt;
  float correction_l = kp * error_l + ki * integral_l + kd * derivative_l;
  error_l_prev = error_l;
  pwm_l_cmd += correction_l * DUTY_MAX;
  pwm_l_cmd = constrain(pwm_l_cmd, -DUTY_MAX, DUTY_MAX);

  float error_r = target_r - v_r;
  integral_r += error_r * dt;
  float derivative_r = (error_r - error_r_prev) / dt;
  float correction_r = kp * error_r + ki * integral_r + kd * derivative_r;
  error_r_prev = error_r;
  pwm_r_cmd += correction_r * DUTY_MAX;
  pwm_r_cmd = constrain(pwm_r_cmd, -DUTY_MAX, DUTY_MAX);

//  Serial.printf("Motor PWM_L: %.2f, PWM_R %.2f \n", pwm_l_cmd, pwm_r_cmd);/
  driveMotorA(pwm_l_cmd);
  driveMotorB(pwm_r_cmd);

  // === Odometry ===
  float v = (v_r + v_l) / 2.0;
  float w = (v_r - v_l) / BASE_WIDTH;

  float dx = v * cos(theta) * (dt/1000);
  float dy = v * sin(theta) * (dt/1000);
  float dtheta = w * dt/1000;

  x += dx;
  y += dy;
  theta += dtheta;

  // === Serial Output ===
//  Serial.printf("CMD_VEL: %.2f %.2f | ACT_VEL: %.2f %.2f | PO/
//  Serial.printf("CMD_VEL: %.2f %.2f | ACT_VEL: %.2f %.2f\n", target_l, target_r, v_l, v_r);
  Serial.printf("POS: x=%.2f y=%.2f theta=%.2f\n", x, y, theta);


  // === Serial Input (from Pi) ===
  if (Serial.available()) {
    String cmd = Serial.readStringUntil('\n');
    float linear, angular;
    if (sscanf(cmd.c_str(), "%f %f", &linear, &angular) == 2) {
      // Convert to wheel targets
      target_l = linear - (angular * BASE_WIDTH / 2.0);
      target_r = linear + (angular * BASE_WIDTH / 2.0);
    }
  }

  last_time = now;
}
