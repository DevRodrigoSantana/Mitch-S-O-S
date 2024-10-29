import cv2
import mediapipe as mp
import speech_recognition as sr
import threading
import time
import websocket
import json
import webbrowser
import folium

# Inicialização do MediaPipe Hands
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(min_detection_confidence=0.7)

# Inicialização do OpenCV para captura de vídeo
cap = cv2.VideoCapture(0)
window_width = 640
window_height = 480

# Inicialização do reconhecimento de fala
reconhecedor = sr.Recognizer()
socorro_detectado = False
tempo_socorro = 0  # Para rastrear o tempo desde a última detecção da palavra "socorro"


ultimo_envio = 0 
socorro_enviado = False  
ws = None  

def mostrar_mapa(lat, lng):
    # Criar um mapa centrado na localização
    mapa = folium.Map(location=[lat, lng], zoom_start=15)

    # Adicionar um marcador para a localização
    folium.Marker([lat, lng], popup="Localização: {}, {}".format(lat, lng)).add_to(mapa)

    # Salvar o mapa em um arquivo HTML
    mapa.save("mapa.html")
    print("Mapa salvo como mapa.html. Abra este arquivo no navegador para visualizar.")

# Função para captura de áudio
def capturar_audio():
    global socorro_detectado, tempo_socorro
    with sr.Microphone() as fonte:
        print("Ajustando o ruído do fundo.")
        reconhecedor.adjust_for_ambient_noise(fonte)  # Ajuste para o ruído de fundo
        print("Pronto para ouvir. Diga algo.")

        while True:
            try:
                audio = reconhecedor.listen(fonte)
                texto = reconhecedor.recognize_google(audio, language="pt-BR")
                
                print(f"Reconhecido: {texto}")

                # Verificar se a palavra "socorro" foi dita
                if "socorro" in texto.lower():
                    if not socorro_detectado or (time.time() - tempo_socorro >= 5):
                        socorro_detectado = True
                        tempo_socorro = time.time()  # Atualiza o tempo da última detecção
                        print("Você disse 'socorro'!")

            except sr.UnknownValueError:
                continue
            except sr.RequestError as e:
                print(f"Erro ao conectar ao serviço de reconhecimento de fala: {e}")

# Função para receber mensagens do WebSocket
def on_message(ws, message):
    print(f"Mensagem recebida: {message}")  
    try:
        data = json.loads(message)
        print(f"Dados decodificados: {data}") 

        if 'lat' in data and 'lng' in data:
            lat = data['lat']
            lng = data['lng']
            print(f"Localização recebida: Latitude: {lat}, Longitude: {lng}")

            mostrar_mapa(lat, lng)
            webbrowser.open("mapa.html")  
        else:
            print("Chaves 'lat' ou 'lng' não encontradas na mensagem.")
    except json.JSONDecodeError:
        print("Erro: A mensagem recebida não é um JSON válido.")
    except Exception as e:
        print(f"Erro ao processar a mensagem: {e}")

# Função para configurar o WebSocket
def iniciar_websocket():
    global ws
    ws = websocket.WebSocketApp("ws://localhost:8080/ws1",
                                  on_message=on_message)
    ws.run_forever()

# Thread para captura de áudio
captura_audio_thread = threading.Thread(target=capturar_audio)
captura_audio_thread.daemon = True
captura_audio_thread.start()

# Thread para o WebSocket
websocket_thread = threading.Thread(target=iniciar_websocket)
websocket_thread.daemon = True
websocket_thread.start()

while cap.isOpened():
    success, imagem = cap.read()
    if not success:
        break

    window_width =  854
    window_height = 480

    # Converter a imagem para RGB e inverter a imagem
    imagem = cv2.resize(imagem, (window_width, window_height))
    imagem = cv2.flip(imagem, 1)
    imagem_rgb = cv2.cvtColor(imagem, cv2.COLOR_BGR2RGB)
    imagem_rgb.flags.writeable = False

    # Processar a imagem e detectar as mãos
    resultados = hands.process(imagem_rgb)

    # Converter de volta para BGR
    imagem_rgb.flags.writeable = True
    imagem = cv2.cvtColor(imagem_rgb, cv2.COLOR_RGB2BGR)

    # Verificar se as mãos foram detectadas
    if resultados.multi_hand_landmarks:
        maos_count = len(resultados.multi_hand_landmarks)
        todos_dedos_levantados_mão1 = True
        todos_dedos_levantados_mão2 = True
        indicador_levantado_mão1 = False
        indicador_levantado_mão2 = False

        for i, hand_landmarks in enumerate(resultados.multi_hand_landmarks):
            # Desenhar as landmarks das mãos
            mp.solutions.drawing_utils.draw_landmarks(
                imagem, hand_landmarks, mp_hands.HAND_CONNECTIONS)

            # Verificar se todos os dedos estão levantados
            dedos_levantados = [
                (hand_landmarks.landmark[8].y < hand_landmarks.landmark[6].y),  # Indicador
                (hand_landmarks.landmark[12].y < hand_landmarks.landmark[10].y),  # Médio
                (hand_landmarks.landmark[16].y < hand_landmarks.landmark[14].y),  # Anelar
                (hand_landmarks.landmark[20].y < hand_landmarks.landmark[18].y)   # Mínimo
            ]

            if all(dedos_levantados):
                if i == 0:
                    todos_dedos_levantados_mão1 = True
                elif i == 1:
                    todos_dedos_levantados_mão2 = True
            else:
                if i == 0:
                    todos_dedos_levantados_mão1 = False
                elif i == 1:
                    todos_dedos_levantados_mão2 = False

            
            indicador_levantado = (hand_landmarks.landmark[8].y < hand_landmarks.landmark[6].y) and \
                                  not (hand_landmarks.landmark[5].y < hand_landmarks.landmark[6].y)  # MCP < PIP
            if indicador_levantado:
                if i == 0:
                    indicador_levantado_mão1 = True
                elif i == 1:
                    indicador_levantado_mão2 = True

        
        if maos_count == 2:  # Se há duas mãos
            if todos_dedos_levantados_mão1 and todos_dedos_levantados_mão2:
                cv2.putText(imagem, "Preciso de ajuda!", (50, 50),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

                if time.time() - ultimo_envio >= 5:  
                    print("Enviado: socorro")
                    ws.send("socorro")
                    ultimo_envio = time.time()
                    socorro_enviado = True  

            elif(todos_dedos_levantados_mão1 and not todos_dedos_levantados_mão2) or ( todos_dedos_levantados_mão2 and not todos_dedos_levantados_mão1 ):
                cv2.putText(imagem, "Parar", (50, 50),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        
                if time.time() - ultimo_envio >= 3:  
                    ws.send("parar")  
                    print("Enviado: parar")
                    ultimo_envio = time.time() 

            elif indicador_levantado_mão1 or indicador_levantado_mão2:
                cv2.putText(imagem, "Girar", (50, 100),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)

                if time.time() - ultimo_envio >= 3:  
                    ws.send("girar")  
                    print("Enviado: girar")
                    ultimo_envio = time.time()  

        elif maos_count == 1:  # Se há apenas uma mão
            if todos_dedos_levantados_mão1:
                cv2.putText(imagem, "Preciso de Ajuda!", (50, 50),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

                if time.time() - ultimo_envio >= 5:  
                    ws.send("socorro")  
                    print("Enviado: socorro")
                    ultimo_envio = time.time()  

            elif indicador_levantado_mão1:
                cv2.putText(imagem, "Girar!", (50, 100),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)

                if time.time() - ultimo_envio >= 3:  
                    ws.send("girar")  
                    print("Enviado: girar")
                    ultimo_envio = time.time() 
            else:  # Se a mão estiver fechada
                cv2.putText(imagem, "Parar", (50, 50),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

                if time.time() - ultimo_envio >= 3:  
                    ws.send("parar")  
                    print("Enviado: parar")
                    ultimo_envio = time.time() 

    # Exibir a imagem com as detecções
    cv2.imshow("Detecção de Mãos", imagem)

    if cv2.waitKey(5) & 0xFF == 27:  # Pressione 'Esc' para sair
        break

cap.release()
cv2.destroyAllWindows()
