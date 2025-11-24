import cv2
from ultralytics import YOLO
import time
import serial

# --- CONFIGURAÇÃO DA SERIAL (ESP32) ---
# Tente conectar ao Arduino/ESP32
try:
    # Troque 'COM3' pela sua porta. Baudrate 9600 tem que ser igual ao do ESP32
    arduino = serial.Serial('COM4', 9600, timeout=1)
    time.sleep(2)  # Espera 2 segundos pro ESP32 reiniciar a conexão
    print("✅ Conectado ao ESP32!")
except:
    print("❌ ATENÇÃO: ESP32 não encontrado. O código vai rodar sem ele.")
    arduino = None

# --- CONFIGURAÇÃO DA CÂMERA ---
# Mantive suas configurações do DroidCam
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

model = YOLO("best.pt")
LIMITE_CONFIANCA = 0.8
LINHA_GATILHO = 300

ultimo_tempo_comando = 0
delay_entre_comandos = 2.0

while True:
    sucesso, frame = cap.read()
    if not sucesso:
        break

    resultados = model(frame, verbose=False)
    frame_anotado = frame.copy()

    # Desenha linha de gatilho
    cv2.line(frame_anotado, (LINHA_GATILHO, 0),
             (LINHA_GATILHO, 480), (0, 255, 0), 2)

    for resultado in resultados:
        frame_anotado = resultado.plot()

        for box in resultado.boxes:
            confianca = float(box.conf[0])
            x1, y1, x2, y2 = box.xyxy[0]
            centro_x = int((x1 + x2) / 2)

            agora = time.time()

            if confianca > LIMITE_CONFIANCA and (agora - ultimo_tempo_comando) > delay_entre_comandos:
                if centro_x > LINHA_GATILHO:

                    classe_id = int(box.cls[0])
                    nome_objeto = model.names[classe_id]

                    if nome_objeto == "little-box":
                        print(f"📦 LITTLE-BOX DETECTADA! Enviando sinal '1'...")

                        # --- ENVIA PARA O ESP32 ---
                        if arduino:
                            arduino.write(b'1')  # O 'b' transforma em bytes

                        ultimo_tempo_comando = time.time()

                    elif nome_objeto == "outra_coisa":
                        print("Objeto rejeitado. Enviando sinal '2'...")
                        if arduino:
                            arduino.write(b'2')
                        ultimo_tempo_comando = time.time()

    cv2.imshow("Seletor", frame_anotado)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Fecha tudo direitinho
if arduino:
    arduino.close()
cap.release()
cv2.destroyAllWindows()
