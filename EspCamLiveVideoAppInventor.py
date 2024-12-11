import camera
import network
import socket
import time

# Configuración de Wi-Fi
def connect_wifi(ssid, password):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    print("Conectando a Wi-Fi...")
    wlan.connect(ssid, password)
    while not wlan.isconnected():
        time.sleep(1)
        print(".", end="")
    print("\nConexión Wi-Fi establecida:", wlan.ifconfig())
    return wlan.ifconfig()[0]  # Retorna la dirección IP asignada

# Inicializar la cámara
def init_camera():
    try:
        camera.init(0, format=camera.JPEG)
        camera.framesize(camera.FRAME_QVGA)  # Tamaño de imagen
        camera.flip(0)
        camera.mirror(0)
        camera.saturation(0)
        camera.brightness(0)
        print("Cámara inicializada")
    except Exception as e:
        print("Error al inicializar la cámara:", str(e))

# Generar flujo MJPEG
def generate_mjpeg():
    while True:
        try:
            img = camera.capture()
            if img:
                yield b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + img + b"\r\n"
        except Exception as e:
            print("Error en flujo MJPEG:", e)
            break

# Servidor web
def start_web_server(ip):
    addr = socket.getaddrinfo(ip, 80)[0][-1]
    s = socket.socket()
    s.bind(addr)
    s.listen(5)
    print(f"Servidor web escuchando en http://{ip}:80")

    while True:
        cl, addr = s.accept()
        print("Cliente conectado desde", addr)
        request = cl.recv(1024).decode('utf-8')
        print("Solicitud recibida:", request)

        if "/capture" in request:  # Capturar y enviar una imagen
            print("Capturando imagen...")
            img = camera.capture()
            if img:
                response = b"""HTTP/1.1 200 OK
Content-Type: image/jpeg

""" + img
                cl.send(response)
            else:
                cl.send(b"HTTP/1.1 500 Internal Server Error\r\n\r\nError al capturar la imagen")

        elif "/stream" in request:  # Enviar flujo de video MJPEG
            print("Iniciando streaming MJPEG...")
            headers = b"""HTTP/1.1 200 OK
Content-Type: multipart/x-mixed-replace; boundary=frame

"""
            cl.send(headers)
            for frame in generate_mjpeg():
                try:
                    cl.send(frame)
                except Exception as e:
                    print("Cliente desconectado del streaming:", str(e))
                    break

        cl.close()

# Configuración principal
def main():
    SSID = "HogarReyes#"  # Cambia por tu SSID
    PASSWORD = "FueraPiratas2023.."  # Cambia por tu contraseña

    # Conectar al Wi-Fi
    ip = connect_wifi(SSID, PASSWORD)

    # Inicializar la cámara
    init_camera()

    # Iniciar el servidor web
    start_web_server(ip)

# Ejecutar el programa
if __name__ == "__main__":
    main()
