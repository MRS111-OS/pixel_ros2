#include <Arduino.h>

#define PI 3.14159265f

// === Motor Pins ===
#define ENABLE 36

#define PWM1 3
#define IN1 4
#define IN2 5
#define PWM2 14
#define INB1 18
#define INB2 21

// === Encoder Pins ===
#define M1_ENC_A 17
#define M1_ENC_B 38
#define M2_ENC_A 12
#define M2_ENC_B 13

#define POWER_OUTPUT 25

// === Constants ===
#define PWM_FREQ     10000
#define PWM_RES_BITS 8
#define DUTY_MAX     255

#define WHEEL_RADIUS 0.0325  // meters
#define BASE_WIDTH   0.18   // distance between wheels (meters)
#define TICKS_PER_REV 1000   // encoder resolution
#define GEAR_RATIO 1.0

#define CMD_TIMEOUT 1000  // Stop motors if no command for 1 second
#define LOOP_RATE 50      // 50ms = 20Hz

// === PID parameters ===
float kp = 0.3, ki = 0.0, kd = 0.00;

// === State ===
volatile long m1_ticks = 0;
volatile long m2_ticks = 0;
volatile uint8_t last_m1_enc = 0;
volatile uint8_t last_m2_enc = 0;

// Previous tick counts for delta calculation
long prev_m1_ticks = 0;
long prev_m2_ticks = 0;

float m1_speed = 0, m2_speed = 0;
float target_l = 0, target_r = 0;
float pwm_l_cmd = 0, pwm_r_cmd = 0;
float integral_l = 0, integral_r = 0;
float error_l_prev = 0, error_r_prev = 0;

unsigned long last_time = 0;
unsigned long last_cmd_time = 0;

// === Odometry ===
float x = 0, y = 0, theta = 0;

// === Serial Input Buffer ===
String inputBuffer = "";

void IRAM_ATTR updateEnc1() {
  uint8_t MSB = digitalRead(M1_ENC_A);
  uint8_t LSB = digitalRead(M1_ENC_B);
  uint8_t enc = (MSB << 1) | LSB;
  uint8_t sum = (last_m1_enc << 2) | enc;

  if (sum == 0b0001 || sum == 0b0111 || sum == 0b1110 || sum == 0b1000) {
    m1_ticks++;
  }
  else if (sum == 0b0010 || sum == 0b1011 || sum == 0b1101 || sum == 0b0100) {
    m1_ticks--;
  }

  last_m1_enc = enc;
}

void IRAM_ATTR updateEnc2() {
  uint8_t MSB = digitalRead(M2_ENC_A);
  uint8_t LSB = digitalRead(M2_ENC_B);
  uint8_t enc = (MSB << 1) | LSB;
  uint8_t sum = (last_m2_enc << 2) | enc;

  if (sum == 0b0001 || sum == 0b0111 || sum == 0b1110 || sum == 0b1000) {
    m2_ticks++;
  }
  else if (sum == 0b0010 || sum == 0b1011 || sum == 0b1101 || sum == 0b0100) {
    m2_ticks--;
  }

  last_m2_enc = enc;
}

void driveMotorA(float pwm) {
  bool forward = pwm >= 0;
  digitalWrite(IN1, forward ? HIGH : LOW);
  digitalWrite(IN2, forward ? LOW : HIGH);
  ledcWrite(PWM1, abs((int)pwm));
}

void driveMotorB(float pwm) {
  // INVERTED: Motor B is wired backwards, so negate the PWM
  pwm = -pwm;
  bool forward = pwm >= 0;
  digitalWrite(INB1, forward ? HIGH : LOW);
  digitalWrite(INB2, forward ? LOW : HIGH);
  ledcWrite(PWM2, abs((int)pwm));
}

void stopMotors() {
  driveMotorA(0);
  driveMotorB(0);
  target_l = 0;
  target_r = 0;
  pwm_l_cmd = 0;
  pwm_r_cmd = 0;
  integral_l = 0;
  integral_r = 0;
  error_l_prev = 0;
  error_r_prev = 0;
}

// Conversion functions
float ticksToMeters(long ticks) {
  // Distance per tick = (2 * PI * wheel_radius) / ticks_per_rev
  float distance_per_tick = (2.0 * PI * WHEEL_RADIUS) / TICKS_PER_REV;
  return ticks * distance_per_tick;
}

float ticksToRadians(long ticks) {
  // Angle per tick = (2 * PI) / ticks_per_rev
  return (ticks * 2.0 * PI) / TICKS_PER_REV;
}

void testWheelMapping() {
  Serial.println("\n=== WHEEL MAPPING TEST ===");
  Serial.println("Make sure robot wheels can spin freely!");
  Serial.println("Testing in 3 seconds...");
  delay(3000);
  
  Serial.println("\nTesting LEFT wheel (Motor A)...");
  
  // Reset encoders
  noInterrupts();
  m1_ticks = 0;
  m2_ticks = 0;
  interrupts();
  
  // Drive Motor A forward for 2 seconds
  driveMotorA(150);
  delay(2000);
  driveMotorA(0);
  delay(500);
  
  // Check which encoder counted
  long m1_count, m2_count;
  noInterrupts();
  m1_count = m1_ticks;
  m2_count = m2_ticks;
  interrupts();
  
  Serial.printf("Motor A -> M1_ticks=%ld, M2_ticks=%ld\n", m1_count, m2_count);
  if (abs(m1_count) > abs(m2_count)) {
    Serial.println("✓ Motor A is correctly mapped to Encoder 1 (LEFT)");
  } else {
    Serial.println("✗ Motor A is mapped to Encoder 2 - SWAP ENCODER PINS!");
  }
  
  delay(1000);
  
  // Reset and test Motor B
  Serial.println("\nTesting RIGHT wheel (Motor B)...");
  noInterrupts();
  m1_ticks = 0;
  m2_ticks = 0;
  interrupts();
  
  driveMotorB(150);
  delay(2000);
  driveMotorB(0);
  delay(500);
  
  noInterrupts();
  m1_count = m1_ticks;
  m2_count = m2_ticks;
  interrupts();
  
  Serial.printf("Motor B -> M1_ticks=%ld, M2_ticks=%ld\n", m1_count, m2_count);
  if (abs(m2_count) > abs(m1_count)) {
    Serial.println("✓ Motor B is correctly mapped to Encoder 2 (RIGHT)");
  } else {
    Serial.println("✗ Motor B is mapped to Encoder 1 - SWAP ENCODER PINS!");
  }
  
  Serial.println("\n=== TEST COMPLETE ===");
  Serial.println("If swapping is needed, exchange M1_ENC and M2_ENC pin definitions\n");
  
  // Reset everything
  stopMotors();
}

void processSerialInput() {
  // Non-blocking serial read
  while (Serial.available() > 0) {
    char c = Serial.read();
    
    if (c == '\n' || c == '\r') {
      if (inputBuffer.length() > 0) {
        // Process the complete command
        inputBuffer.trim();
        
        float linear, angular;
        if (sscanf(inputBuffer.c_str(), "%f %f", &linear, &angular) == 2) {
          target_l = linear - (angular * BASE_WIDTH / 2.0);
          target_r = linear + (angular * BASE_WIDTH / 2.0);
          last_cmd_time = millis();
          Serial.printf("RX: lin=%.2f ang=%.2f -> L=%.2f R=%.2f\n", 
                        linear, angular, target_l, target_r);
        }
        
        inputBuffer = "";
      }
    } else {
      inputBuffer += c;
      // Prevent buffer overflow
      if (inputBuffer.length() > 50) {
        inputBuffer = "";
      }
    }
    
    // Yield to prevent watchdog issues
    yield();
  }
}

void setup() {
  Serial.begin(115200);
  
  // Wait for serial to be ready
  while (!Serial && millis() < 5000) {
    delay(10);
  }
  
  Serial.println("\n=== ESP32 Differential Drive Started ===");

  // Motor Pins
  pinMode(IN1, OUTPUT);
  pinMode(IN2, OUTPUT);
  pinMode(INB1, OUTPUT);
  pinMode(INB2, OUTPUT);
  pinMode(POWER_OUTPUT, OUTPUT);

  ledcAttach(PWM1, PWM_FREQ, PWM_RES_BITS);
  ledcAttach(PWM2, PWM_FREQ, PWM_RES_BITS);
  ledcWrite(PWM1, 0);
  ledcWrite(PWM2, 0);

  // Encoder Pins
  pinMode(M1_ENC_A, INPUT_PULLUP);
  pinMode(M1_ENC_B, INPUT_PULLUP);
  pinMode(M2_ENC_A, INPUT_PULLUP);
  pinMode(M2_ENC_B, INPUT_PULLUP);

  //EnableMotors
  pinMode(ENABLE, OUTPUT);
  digitalWrite(ENABLE, HIGH);
  digitalWrite(POWER_OUTPUT, HIGH);

  attachInterrupt(digitalPinToInterrupt(M1_ENC_A), updateEnc1, CHANGE);
  attachInterrupt(digitalPinToInterrupt(M1_ENC_B), updateEnc1, CHANGE);
  attachInterrupt(digitalPinToInterrupt(M2_ENC_A), updateEnc2, CHANGE);
  attachInterrupt(digitalPinToInterrupt(M2_ENC_B), updateEnc2, CHANGE);

  last_time = millis();
  last_cmd_time = millis();
  
  Serial.println("Initialization complete!");
  
  // Run wheel mapping test
  // testWheelMapping();
  
  Serial.println("Waiting for ROS connection...");
}

void loop() {
  unsigned long now = millis();
  float dt = (now - last_time);
  
  // Always process serial input (non-blocking)
  processSerialInput();
  
  // Fixed rate loop - run at LOOP_RATE
  if (dt < LOOP_RATE) {
    delay(1);  // Small delay to prevent tight loop and feed watchdog
    return;
  }

  // Check for command timeout
  if (now - last_cmd_time > CMD_TIMEOUT) {
    if (target_l != 0 || target_r != 0) {
      stopMotors();
    }
  }

  // Read current encoder ticks - minimize time with interrupts disabled
  long current_m1_ticks, current_m2_ticks;
  noInterrupts();
  current_m1_ticks = m1_ticks;
  current_m2_ticks = m2_ticks;
  interrupts();

  // Calculate delta ticks since last reading
  long delta_m1_ticks = current_m1_ticks - prev_m1_ticks;
  long delta_m2_ticks = current_m2_ticks - prev_m2_ticks;
  
  // Store current ticks for next iteration
  prev_m1_ticks = current_m1_ticks;
  prev_m2_ticks = current_m2_ticks;

  // Convert delta ticks to distance traveled by each wheel (in meters)
  float delta_left = ticksToMeters(delta_m1_ticks);
  float delta_right = ticksToMeters(delta_m2_ticks);

  // === Odometry Calculation (Differential Drive) ===
  // Calculate change in orientation (theta)
  float delta_theta = (delta_right - delta_left) / BASE_WIDTH;
  
  // Calculate linear distance traveled by robot center
  float delta_s = (delta_right + delta_left) / 2.0;
  
  // Update global pose using current orientation
  // This is the correct order: use current theta BEFORE updating it
  float delta_x = delta_s * cos(theta);
  float delta_y = delta_s * sin(theta);
  
  // Update pose
  x += delta_x;
  y += delta_y;
  theta += delta_theta;
  
  // Normalize theta to [-PI, PI]
  while (theta > PI) theta += 2.0 * PI;
  while (theta < -PI) theta -= 2.0 * PI;

  // === Velocity Calculation (for PID and reporting) ===
  // Convert dt to seconds
  float dt_sec = dt / 1000.0;
  
  // Calculate wheel velocities (m/s)
  float v_l = delta_left / dt_sec;
  float v_r = delta_right / dt_sec;
  
  // Calculate robot linear and angular velocities
  float v_robot = delta_s / dt_sec;  // Linear velocity (m/s)
  float w_robot = delta_theta / dt_sec;  // Angular velocity (rad/s)

  // === PID Control ===
  float error_l = target_l - v_l;
  integral_l += error_l * dt_sec;
  float derivative_l = (error_l - error_l_prev) / dt_sec;
  float correction_l = kp * error_l + ki * integral_l + kd * derivative_l;
  error_l_prev = error_l;
  pwm_l_cmd += correction_l * DUTY_MAX;
  pwm_l_cmd = constrain(pwm_l_cmd, -DUTY_MAX, DUTY_MAX);

  float error_r = target_r - v_r;
  integral_r += error_r * dt_sec;
  float derivative_r = (error_r - error_r_prev) / dt_sec;
  float correction_r = kp * error_r + ki * integral_r + kd * derivative_r;
  error_r_prev = error_r;
  pwm_r_cmd += correction_r * DUTY_MAX;
  pwm_r_cmd = constrain(pwm_r_cmd, -DUTY_MAX, DUTY_MAX);

  driveMotorA(pwm_l_cmd);
  driveMotorB(pwm_r_cmd);

  // === Serial Output ===
  //Serial.printf("Ticks: L=%ld R=%ld | Delta: L=%ld R=%ld\n", 
  //              current_m1_ticks, current_m2_ticks, delta_m1_ticks, delta_m2_ticks);
  //Serial.printf("Vel: vL=%.3f vR=%.3f | Robot: v=%.3f w=%.3f\n", 
  //              v_l, v_r, v_robot, w_robot);
  Serial.printf("POS: x=%.2f y=%.2f theta=%.2f\n", 
                x, y, theta);
  //Serial.println("---");

  last_time = now;
  
  // Feed the watchdog
  yield();
}