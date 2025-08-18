#include <Arduino.h>

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

// === Encoder state tracking ===
volatile long m1_ticks = 0;
volatile long m2_ticks = 0;

volatile uint8_t m1_lastEncoded = 0;
volatile uint8_t m2_lastEncoded = 0;

#define PWM_FREQ     1000
#define PWM_RES_BITS 8
#define DUTY_MAX     255

// === Motor A ISR ===
void IRAM_ATTR m1_updateEncoder() {
  uint8_t MSB = digitalRead(M1_ENC_A);
  uint8_t LSB = digitalRead(M1_ENC_B);

  uint8_t encoded = (MSB << 1) | LSB;
  uint8_t sum = (m1_lastEncoded << 2) | encoded;

  if (sum == 0b0001 || sum == 0b0111 || sum == 0b1110 || sum == 0b1000)
    m1_ticks++;
  else if (sum == 0b0010 || sum == 0b1011 || sum == 0b1101 || sum == 0b0100)
    m1_ticks--;

  m1_lastEncoded = encoded;
}

// === Motor B ISR ===
void IRAM_ATTR m2_updateEncoder() {
  uint8_t MSB = digitalRead(M2_ENC_A);
  uint8_t LSB = digitalRead(M2_ENC_B);

  uint8_t encoded = (MSB << 1) | LSB;
  uint8_t sum = (m2_lastEncoded << 2) | encoded;

  if (sum == 0b0001 || sum == 0b0111 || sum == 0b1110 || sum == 0b1000)
    m2_ticks++;
  else if (sum == 0b0010 || sum == 0b1011 || sum == 0b1101 || sum == 0b0100)
    m2_ticks--;

  m2_lastEncoded = encoded;
}

// === Setup ===
void setup() {
  Serial.begin(115200);
  delay(500);
  Serial.println("ESP32 Motor + Quadrature Encoder ISR");

  pinMode(ENABLE, OUTPUT);

  pinMode(IN1, OUTPUT);
  pinMode(IN2, OUTPUT);
  pinMode(INB1, OUTPUT);
  pinMode(INB2, OUTPUT);

  ledcAttach(PWM1, PWM_FREQ, PWM_RES_BITS);
  ledcWrite(PWM1, 0);
  ledcAttach(PWM2, PWM_FREQ, PWM_RES_BITS);
  ledcWrite(PWM2, 0);

  // Encoder pins
  pinMode(M1_ENC_A, INPUT_PULLUP);
  pinMode(M1_ENC_B, INPUT_PULLUP);
  pinMode(M2_ENC_A, INPUT_PULLUP);
  pinMode(M2_ENC_B, INPUT_PULLUP);

  // Setup initial encoder state
  m1_lastEncoded = (digitalRead(M1_ENC_A) << 1) | digitalRead(M1_ENC_B);
  m2_lastEncoded = (digitalRead(M2_ENC_A) << 1) | digitalRead(M2_ENC_B);

  // Attach interrupts on both encoder pins
  attachInterrupt(digitalPinToInterrupt(M1_ENC_A), m1_updateEncoder, CHANGE);
  attachInterrupt(digitalPinToInterrupt(M1_ENC_B), m1_updateEncoder, CHANGE);
  attachInterrupt(digitalPinToInterrupt(M2_ENC_A), m2_updateEncoder, CHANGE);
  attachInterrupt(digitalPinToInterrupt(M2_ENC_B), m2_updateEncoder, CHANGE);

  // Start motors
  digitalWrite(ENABLE, HIGH);
  driveMotorA(true, 150);
  driveMotorB(false, 150);
}

// === Loop ===
void loop() {
  static long last_m1 = 0, last_m2 = 0;

  delay(1000);

  long current_m1 = m1_ticks;
  long current_m2 = m2_ticks;
  uint8_t m2a = digitalRead(M2_ENC_A);
  uint8_t m2b = digitalRead(M2_ENC_B);
  Serial.printf("encoder pins read: M2A: %hhu M2B: %hhu \n",
                m2a, m2b);
  Serial.printf("M1: %ld ticks (Δ: %ld)\tM2: %ld ticks (Δ: %ld)\n",
                current_m1, current_m1 - last_m1,
                current_m2, current_m2 - last_m2);

  last_m1 = current_m1;
  last_m2 = current_m2;
}

// === Motor control ===
void driveMotorA(bool forward, uint8_t speed) {
  digitalWrite(IN1, forward ? HIGH : LOW);
  digitalWrite(IN2, forward ? LOW : HIGH);
  ledcWrite(PWM1, speed);
}

void driveMotorB(bool forward, uint8_t speed) {
  digitalWrite(INB1, forward ? HIGH : LOW);
  digitalWrite(INB2, forward ? LOW : HIGH);
  ledcWrite(PWM2, speed);
}
