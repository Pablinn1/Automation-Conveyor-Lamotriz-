import cv2
from ultralytics import YOLO
import time  # <--- Importante para controlar o tempo

model = YOLO("best.pt")
cap = cv2.VideoCapture(0)

cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

LIMITE_CONFIANCA = 0.6

# Variável para controlar quando foi o último comando enviado
ultimo_tempo_comando = 0
delay_entre_comandos = 2.0  # Segundos que ele espera para ler o próximo

while True:
    sucesso, frame = cap.read()
    if not sucesso:
        break

    resultados = model(frame, verbose=False)

    for resultado in resultados:
        frame_anotado = resultado.plot()

        for box in resultado.boxes:
            confianca = float(box.conf[0])

            # Verifica se passou tempo suficiente desde o último comando
            agora = time.time()
            if confianca > LIMITE_CONFIANCA and (agora - ultimo_tempo_comando) > delay_entre_comandos:

                classe_id = int(box.cls[0])
                nome_objeto = model.names[classe_id]

                if nome_objeto == "little-box":
                    print(f"📦 LITTLE-BOX detectado! Mover Servo!")
                    # arduino.write(b'1')
                    ultimo_tempo_comando = time.time()  # Reseta o relógio

                else:
                    # Cai aqui se for qualquer outra coisa detectada
                    print("🎉 Caíque é LEGAL é LEGAL É LEGAAAL")
                    # arduino.write(b'2')
                    ultimo_tempo_comando = time.time()  # Reseta o relógio

    cv2.imshow("Seletor", frame_anotado)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
