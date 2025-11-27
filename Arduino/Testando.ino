#include <Servo.h> 

// --- CONFIGURAÇÕES ---
const int PIN_LED = 13;      // Pino do LED
const int PIN_SERVO = 9;     // Pino de sinal do Servo Motor (Verifique sua montagem)
const int TEMPO_ATIVO = 500; // Tempo (ms) que o braço fica ativado antes de voltar

Servo meuServo; 

// --- VARIÁVEIS DE CONTROLE ---
unsigned long tempoAcionamento = 0; // Guarda o momento que o sinal chegou
bool ativado = false;               // Estado atual do sistema

void setup() {
  pinMode(PIN_LED, OUTPUT);
  Serial.begin(9600); 
  
  // Configuração inicial do Servo
  meuServo.attach(PIN_SERVO);
  meuServo.write(0); // Inicia na posição 0 graus (Braço recolhido)
  
  // LED começa desligado
  digitalWrite(PIN_LED, LOW);
}

void loop() {
  // 1. VERIFICA SE CHEGOU COMANDO DO PYTHON
  if (Serial.available() > 0) {
    char comando = Serial.read();

    if (comando == '1') {
      // Ativa o sistema
      digitalWrite(PIN_LED, HIGH);
      meuServo.write(90);  // Move o braço para 90 graus (Empurra o objeto)
      
      tempoAcionamento = millis(); // Marca a hora exata que ativou
      ativado = true;
    }
    // Você pode adicionar o comando '2' para outro servo aqui se quiser
  }

  // 2. VERIFICA SE JÁ DEU O TEMPO DE DESLIGAR (SEM USAR DELAY)
  if (ativado && (millis() - tempoAcionamento >= TEMPO_ATIVO)) {
    // Se passou o tempo estipulado, desliga tudo
    digitalWrite(PIN_LED, LOW);
    meuServo.write(0);     // Recolhe o braço para 0 graus
    ativado = false;
  }
}