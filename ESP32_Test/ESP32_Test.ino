#include <Arduino.h>

#define PI 3.14159265f

// === Motor Pins (ESP32 GPIO numbers) ===
#define LEFT_IN1 13
#define LEFT_IN2 12
#define PWM_LEFT 26

#define RIGHT_IN1 27
#define RIGHT_IN2 14
#define PWM_RIGHT 25

// === Encoder Pins ===
#define ENC_LEFT_A 35
#define ENC_LEFT_B 34
#define ENC_RIGHT_A 33
#define ENC_RIGHT_B 32

// === Constants ===
#define PWM_FREQ 20000
#define PWM_RES_BITS 8
#define DUTY_MAX 255

#define WHEEL_RADIUS 0.0325 // meters
#define BASE_WIDTH 0.18 // meters between wheels
#define TICKS_PER_REV 1000
#define GEAR_RATIO 1.0

// === PID parameters ===
float kp = 0.4, ki = 0.005, kd = 0.00;

// === State ===
volatile long left_ticks = 0;
volatile long right_ticks = 0;
volatile uint8_t last_left_enc = 0;
volatile uint8_t last_right_enc = 0;
 

float target_l = 0.0, target_r = 0.0;
float pwm_l_cmd = 0, pwm_r_cmd = 0;
float integral_l = 0, integral_r = 0;
float error_l_prev = 0, error_r_prev = 0;

unsigned long last_time = 0;

// === Odometry ===
float x = 0, y = 0, theta = 0;

// === Encoder ISR ===
void IRAM_ATTR leftEncoderISR() {
uint8_t MSB = digitalRead(ENC_LEFT_A);
uint8_t LSB = digitalRead(ENC_LEFT_B);
uint8_t enc = (MSB << 1) | LSB;
uint8_t sum = (last_left_enc << 2) | enc;

if (sum == 0b0001 || sum == 0b0111 || sum == 0b1110 || sum == 0b1000)
left_ticks--;
else if (sum == 0b0010 || sum == 0b1011 || sum == 0b1101 || sum == 0b0100)
left_ticks++;

last_left_enc = enc;
}

void IRAM_ATTR rightEncoderISR() {
uint8_t MSB = digitalRead(ENC_RIGHT_A);
uint8_t LSB = digitalRead(ENC_RIGHT_B);
uint8_t enc = (MSB << 1) | LSB;
uint8_t sum = (last_right_enc << 2) | enc;

if (sum == 0b0001 || sum == 0b0111 || sum == 0b1110 || sum == 0b1000)
right_ticks++;
else if (sum == 0b0010 || sum == 0b1011 || sum == 0b1101 || sum == 0b0100)
right_ticks--;

last_right_enc = enc;
}

// === Motor Control ===
void driveLeftMotor(float pwm) {
bool forward = pwm >= 0;
digitalWrite(LEFT_IN1, forward ? LOW : HIGH);
digitalWrite(LEFT_IN2, forward ? HIGH : LOW);
analogWrite(PWM_LEFT, abs((int)pwm));
}

void driveRightMotor(float pwm) {
bool forward = pwm >= 0;
digitalWrite(RIGHT_IN1, forward ? LOW : HIGH);
digitalWrite(RIGHT_IN2, forward ? HIGH : LOW);
analogWrite(PWM_RIGHT, abs((int)pwm));
}

void setup() {
Serial.begin(115200);
delay(1000);
Serial.println("ESP32 Differential Drive (Legacy PWM + PID + Odometry)");

// === Motor Pins ===
pinMode(LEFT_IN1, OUTPUT);
pinMode(LEFT_IN2, OUTPUT);
pinMode(RIGHT_IN1, OUTPUT);
pinMode(RIGHT_IN2, OUTPUT);

// === Set PWM frequency and resolution ===
analogWriteFrequency(PWM_LEFT, PWM_FREQ);
analogWriteFrequency(PWM_RIGHT, PWM_FREQ);
analogWriteResolution(PWM_LEFT, PWM_RES_BITS);
analogWriteResolution(PWM_RIGHT, PWM_RES_BITS);

// === Encoder Pins ===
pinMode(ENC_LEFT_A, INPUT_PULLUP);
pinMode(ENC_LEFT_B, INPUT_PULLUP);
pinMode(ENC_RIGHT_A, INPUT_PULLUP);
pinMode(ENC_RIGHT_B, INPUT_PULLUP);

attachInterrupt(digitalPinToInterrupt(ENC_LEFT_A), leftEncoderISR, CHANGE);
attachInterrupt(digitalPinToInterrupt(ENC_LEFT_B), leftEncoderISR, CHANGE);
attachInterrupt(digitalPinToInterrupt(ENC_RIGHT_A), rightEncoderISR, CHANGE);
attachInterrupt(digitalPinToInterrupt(ENC_RIGHT_B), rightEncoderISR, CHANGE);

last_time = millis();
}

void loop() {
unsigned long now = millis();
float dt = (now - last_time);
if (dt < 40) return; // ~25 Hz loop

// === Read and reset ticks ===
long ticks_l = left_ticks;
long ticks_r = right_ticks;
left_ticks = right_ticks = 0;

// === Compute wheel angular velocity ===
float w_l = (2.0 * PI * (float)ticks_l / (float)TICKS_PER_REV) / (dt / 1000);
float w_r = (2.0 * PI * (float)ticks_r / (float)TICKS_PER_REV) / (dt / 1000);

float v_l = w_l * WHEEL_RADIUS;
float v_r = w_r * WHEEL_RADIUS;

// === PID control ===
float error_l = target_l - v_l;
integral_l += error_l * dt;
float derivative_l = (error_l - error_l_prev) / dt;
float correction_l = kp * error_l + ki * integral_l + kd * derivative_l;
error_l_prev = error_l;
pwm_l_cmd = correction_l * DUTY_MAX;
pwm_l_cmd = constrain(pwm_l_cmd, -DUTY_MAX, DUTY_MAX);

float error_r = target_r - v_r;
integral_r += error_r * dt;
float derivative_r = (error_r - error_r_prev) / dt;
float correction_r = kp * error_r + ki * integral_r + kd * derivative_r;
error_r_prev = error_r;
pwm_r_cmd = correction_r * DUTY_MAX;
pwm_r_cmd = constrain(pwm_r_cmd, -DUTY_MAX, DUTY_MAX);

driveLeftMotor(pwm_l_cmd);
driveRightMotor(pwm_r_cmd);

// === Odometry ===
float v = (v_r + v_l) / 2.0;
float w = (v_r - v_l) / BASE_WIDTH;

float dx = v * cos(theta) * (dt / 1000);
float dy = v * sin(theta) * (dt / 1000);
float dtheta = w * (dt / 1000);

x += dx;
y += dy;
theta += dtheta;

Serial.printf("POS: x=%.3f y=%.3f theta=%.3f\n", x, y, theta);
//Serial.printf("Velocity: vl=%.3f/%.3f vr=%.3f/%.3f \n", target_l, v_l, target_r, v_r);
//Serial.printf("Error: error_l=%.3f error_r=%.3f \n", error_l, error_r);
//Serial.printf("PWM: pwm_l_cmd=%.3f pwm_r_cmd=%.3f \n", pwm_l_cmd, pwm_r_cmd);

// === Serial command input (linear angular or control) ===
if (Serial.available()) {
String cmd = Serial.readStringUntil('\n');
cmd.trim(); // Remove extra spaces/newlines

// Check for restart command (case-insensitive)
if (cmd.equalsIgnoreCase("RESTART")) {
x = 0;
y = 0;
theta = 0;
// Serial.println("Odometry reset: x=0 y=0 theta=0");
}
else {
float linear, angular;
if (sscanf(cmd.c_str(), "%f %f", &linear, &angular) == 2) {
float new_target_l = linear - (angular * BASE_WIDTH / 2.0);
float new_target_r = linear + (angular * BASE_WIDTH / 2.0);
if (abs(new_target_l - target_l) > 0.01 || abs(new_target_r - target_r) > 0.01) {
integral_l = 0;
integral_r = 0;
}
target_l = new_target_l;
target_r = new_target_r;
}
}
}

last_time = now;
}