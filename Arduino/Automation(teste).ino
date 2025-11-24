#include <Servo.h> 

const int Led = 13;

void setup() {
  pinMode(13, OUTPUT);
  Serial.begin(9600); // Tem que ser a mesma velocidade do Python
}

void loop() {
  if (Serial.available() > 0) {
    char comando = Serial.read();

    if (comando == '1') {
      digitalWrite(13, HIGH);
      delay(1000);  
      digitalWrite(13, LOW);  
    }
  }
}