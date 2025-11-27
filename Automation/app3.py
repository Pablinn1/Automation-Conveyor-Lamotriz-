import cv2
from ultralytics import YOLO
import time
import serial

# --- 1. CONFIGURAÇÃO DA SERIAL (ESP32) ---
try:
    # Ajuste a porta COM conforme necessário
    arduino = serial.Serial('COM4', 9600, timeout=1)
    time.sleep(2)
    print("✅ Conectado ao ESP32!")
except Exception as e:
    print(
        f"❌ ATENÇÃO: ESP32 não encontrado ({e}). O código vai rodar em modo Simulação.")
    arduino = None

# --- 2. CONFIGURAÇÃO DA CÂMERA ---
cap = cv2.VideoCapture(0)
# Dica: Se ficar lento, baixe a resolução para 640x480. O YOLO roda mais rápido.
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

# Carrega o modelo
model = YOLO("best.pt")

# --- 3. PARÂMETROS DE CONTROLE ---
LIMITE_CONFIANCA = 0.6  # Reduzi um pouco para garantir que pegue em movimento
LINHA_GATILHO_X = 350   # Onde a ação acontece
LARGURA_ZONA = 20       # Zona de "hysteresis" para evitar disparos múltiplos
# Delay menor, apenas para não spamar o serial (debounce)
DELAY_COMANDO = 0.5

ultimo_tempo_comando = 0

print("🚀 Sistema Iniciado. Pressione 'q' para sair.")

while True:
    sucesso, frame = cap.read()
    if not sucesso:
        print("Erro ao ler câmera.")
        break

    # Pega altura e largura reais da imagem para desenhar a linha corretamente
    altura_img, largura_img = frame.shape[:2]

    # stream=True deixa a inferência um pouco mais rápida e consome menos memória
    resultados = model(frame, stream=True, verbose=False)

    # Processamos os resultados.
    # Nota: Como usamos stream=True, 'resultados' é um gerador.
    for resultado in resultados:
        # Primeiro pegamos a imagem anotada pelo YOLO
        frame_anotado = resultado.plot()

        # AGORA desenhamos a linha e a zona sobre a imagem anotada
        # Desenha a linha de gatilho (Verde)
        cv2.line(frame_anotado, (LINHA_GATILHO_X, 0),
                 (LINHA_GATILHO_X, altura_img), (0, 255, 0), 2)
        # Desenha uma zona transparente (opcional, só visual)
        cv2.line(frame_anotado, (LINHA_GATILHO_X + LARGURA_ZONA, 0),
                 (LINHA_GATILHO_X + LARGURA_ZONA, altura_img), (0, 255, 0), 1)

        for box in resultado.boxes:
            confianca = float(box.conf[0])

            # Só processa se tiver confiança boa
            if confianca > LIMITE_CONFIANCA:
                # Garante conversão segura
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                centro_x = int((x1 + x2) / 2)
                centro_y = int((y1 + y2) / 2)

                # Desenha o ponto central do objeto para facilitar o debug
                cv2.circle(frame_anotado, (centro_x, centro_y),
                           5, (255, 0, 0), -1)

                agora = time.time()

                # --- LÓGICA DE ZONA (Melhor que apenas > linha) ---
                # O objeto precisa estar ENTRE a linha e a margem da zona
                # Isso evita que o sinal seja enviado infinitamente enquanto o objeto
                # estiver no final da tela.
                na_zona_de_gatilho = LINHA_GATILHO_X < centro_x < (
                    LINHA_GATILHO_X + LARGURA_ZONA)
                pode_enviar = (agora - ultimo_tempo_comando) > DELAY_COMANDO

                if na_zona_de_gatilho and pode_enviar:

                    classe_id = int(box.cls[0])
                    nome_objeto = model.names[classe_id]

                    print(
                        f"🎯 ALVO NA ZONA: {nome_objeto} | Conf: {confianca:.2f}")

                    msg = None
                    if nome_objeto == "little-box":  # Verifique se o nome no dataset é exato!
                        msg = b'1'
                        cor_texto = (0, 255, 0)  # Verde
                    elif nome_objeto == "outra_coisa":
                        msg = b'2'
                        cor_texto = (0, 0, 255)  # Vermelho

                    if msg and arduino:
                        arduino.write(msg)
                        print(f"📡 Sinal enviado: {msg}")
                        # Feedback visual na tela
                        cv2.putText(frame_anotado, f"ENVIADO: {msg}", (50, 50),
                                    cv2.FONT_HERSHEY_SIMPLEX, 1, cor_texto, 3)

                    ultimo_tempo_comando = time.time()

    cv2.imshow("Seletor Inteligente", frame_anotado)

    # Sai com 'q'
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Limpeza final
if arduino:
    arduino.close()
cap.release()
cv2.destroyAllWindows()
print("Sistema encerrado.")
