from machine import Pin, PWM, I2C
import time
from ldr import LDR
from ssd1306 import SSD1306_I2C
import network
import socket

# Configuración del hardware
i2c = I2C(0, scl=Pin(18), sda=Pin(19))  # Inicialización de I2C para OLED
oled = SSD1306_I2C(128, 64, i2c)       # Resolución de la pantalla 128x64

led_init = Pin(13, Pin.OUT)            # LED inicial
ldr = LDR(34, min_value=0, max_value=100)  # Sensor LDR
buzzer_ldr = Pin(21, Pin.OUT)          # Zumbador para LDR
pir = Pin(15, Pin.IN)                  # Sensor PIR
buzzer_pir = PWM(Pin(5))               # Zumbador para PIR
buzzer_pir.freq(1000)
trigger = Pin(25, Pin.OUT)             # Trigger del HC-SR04
echo = Pin(26, Pin.IN)                 # Echo del HC-SR04
led = Pin(32, Pin.OUT)                 # LED de alarma

# Variables globales
modo_actual = "ninguno"  # Modo inicial (ninguno)

def main():
    # Ejecutar la secuencia de inicio
    startup_sequence()
    """Función principal."""
    ip = conectar_wifi("HogarReyes#", "FueraPiratas2023..")
    iniciar_servidor(ip)

def conectar_wifi(ssid, password):
    """Conecta al Wi-Fi y devuelve la dirección IP."""
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(ssid, password)
    print("Conectando al Wi-Fi...")
    while not wlan.isconnected():
        time.sleep(1)
    ip = wlan.ifconfig()[0]
    
    print("Conectado a Wi-Fi. Dirección IP:", ip)
    oled.fill(0)  # Limpiar pantalla
    oled.text(ip, 0, 0)  # Mensaje en la pantalla
    oled.show()
    
    return ip

def iniciar_servidor(ip):
    """Inicia el servidor para manejar solicitudes HTTP."""
    global modo_actual

    addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
    s = socket.socket()
    s.bind(addr)
    s.listen(1)
    print(f"Servidor HTTP corriendo en {ip}")

    while True:
        # Manejo de solicitudes y modos
        manejar_solicitudes(s)
        ejecutar_modo()

def manejar_solicitudes(socket_servidor):
    """Escucha las solicitudes HTTP y cambia el modo si es necesario."""
    global modo_actual

    socket_servidor.settimeout(0.1)  # Evitar bloqueo
    try:
        cl, addr = socket_servidor.accept()
        print("Cliente conectado desde", addr)
        request = cl.recv(1024).decode('utf-8')
        print("Solicitud recibida:", request)

        # Procesar la solicitud y cambiar el modo
        if "GET /modo?distancia" in request:
            modo_actual = "distancia"
        elif "GET /modo?luz" in request:
            modo_actual = "luz"
        elif "GET /modo?movimiento" in request:
            modo_actual = "movimiento"
        elif "GET /modo?total" in request:
            modo_actual = "total"

        # Responder al cliente
        cl.send("HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\n")
        cl.send(f"Modo cambiado a: {modo_actual}")
        cl.close()

    except OSError:
        # No hay solicitudes pendientes, continuar
        pass

def ejecutar_modo():
    """Ejecuta el modo actual repetidamente."""
    global modo_actual
    if modo_actual == "distancia":
        modo_distancia()
    elif modo_actual == "luz":
        modo_luz()
    elif modo_actual == "movimiento":
        modo_movimiento()
    elif modo_actual == "total":
        modo_total()

def modo_distancia():
    oled.fill(0)  # Limpiar pantalla
    oled.text("Modo distancia", 0, 0)  # Mensaje en la pantalla
    oled.show()
    
    """Modo distancia: mide distancia con el sensor HC-SR04."""
    trigger.off()
    time.sleep_us(2)
    trigger.on()
    time.sleep_us(10)
    trigger.off()

    while echo.value() == 0:
        start_time = time.ticks_us()
    while echo.value() == 1:
        end_time = time.ticks_us()

    duration = time.ticks_diff(end_time, start_time)
    distance = (duration * 0.0343) / 2
    print("Distancia medida:", distance, "cm")

    if distance <= 30:
        print("Distancia menor a 30 cm, activando alarmas")
        buzzer_ldr.on()
        buzzer_pir.duty(512)
        led.on()
        time.sleep(3)
        buzzer_ldr.off()
        buzzer_pir.duty(0)
        led.off()

# Declarar una variable global para rastrear el estado previo
previous_state = "low"  # Estado inicial (puede ajustarse según las condiciones del entorno)

def modo_luz():
    oled.fill(0)  # Limpiar pantalla
    oled.text("Modo Luz", 0, 0)  # Mensaje en la pantalla
    oled.show()
    
    """Modo luz: detecta cambios en los niveles de luz utilizando el LDR."""
    global previous_state  # Acceder y modificar la variable global

    # Leer el valor del LDR
    lux_value = ldr.value()  # Valor normalizado del LDR (entre min_value y max_value)
    print("Nivel de luz:", lux_value)

    # Determinar el estado actual basado en los umbrales
    if lux_value < 52:
        current_state = "low"  # Luz baja
    elif lux_value > 60:
        current_state = "high"  # Luz alta
    else:
        current_state = previous_state  # Mantener el estado anterior si está en zona intermedia

    # Detectar cambios de estado entre luz baja y alta
    if previous_state != current_state:
        if current_state == "low":
            print("Cambio detectado: De luz alta a luz baja")
            beep_low()
        elif current_state == "high":
            print("Cambio detectado: De luz baja a luz alta")
            beep_high()

    # Actualizar el estado previo
    previous_state = current_state

def modo_movimiento():
    oled.fill(0)  # Limpiar pantalla
    oled.text("modo Movimiento", 0, 0)  # Mensaje en la pantalla
    oled.show()
    
    """Modo movimiento: detecta movimiento con el sensor PIR."""
    if pir.value() == 1:
        print("Movimiento detectado")
        buzzer_pir.duty(512)
        time.sleep(3)
        buzzer_pir.duty(0)
    else:
        print("Sin movimiento")

def modo_total():
    oled.fill(0)  # Limpiar pantalla
    oled.text("modo Total", 0, 0)  # Mensaje en la pantalla
    oled.show()
    
    """Modo total: combina todos los sensores."""
    modo_distancia()
    modo_luz()
    modo_movimiento()

# Función para pitidos rápidos (luz alta)
def beep_high():
    for _ in range(3):  # Tres pitidos rápidos
        buzzer_ldr.on()
        time.sleep(0.2)
        buzzer_ldr.off()
        time.sleep(0.2)

# Función para pitidos largos (luz baja)
def beep_low():
    for _ in range(2):  # Dos pitidos largos
        buzzer_ldr.on()
        time.sleep(1)
        buzzer_ldr.off()
        time.sleep(0.5)

def startup_sequence():
    # Parpadear LED inicial tres veces
    for _ in range(3):
        led_init.on()
        time.sleep(1)
        led_init.off()
        time.sleep(0.5)

    # Mostrar mensaje en pantalla OLED
    oled.fill(0)  # Limpiar pantalla
    oled.text("Iniciando sistema", 0, 0)  # Mensaje en la pantalla
    oled.show()
    time.sleep(3)  # Mantener el mensaje durante 3 segundos

    # Borrar pantalla OLED
    oled.fill(0)
    oled.show()
    time.sleep(1)  # Esperar 1 segundo antes de comenzar

    buzzer_ldr.off()  # Desactiva el zumbador para LDR
    buzzer_pir.duty(0)  # Desactiva el zumbador para PIR


# Iniciar el programa
main()
