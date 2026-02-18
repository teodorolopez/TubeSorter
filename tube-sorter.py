import os
import time
import sys

try:
    INTERVAL = float(os.getenv('INTERVAL', '24'))
except ValueError:
    print("Error: INTERVAL debe ser un número válido. Usando valor predeterminado de 24 horas.")
    INTERVAL = 24.0

INTERVAL_SECONDS = INTERVAL * 3600

SECRETS_DIR = os.getenv('SECRETS_DIR', '/app/secrets')
CONFIG_DIR = os.getenv('CONFIG_DIR', '/app/config')

print(f"--- Iniciando Script ---")
print(f"Modo: Ciclo infinito cada {INTERVAL} horas")
print(f"Leyendo archivos de: {SECRETS_DIR}")
print(f"Guardando resultados en: {CONFIG_DIR}")

def tarea_youtube():
    print(f"[{time.strftime('%H:%M:%S')}] Conectando con YouTube API... (Simulado)")
    # Aquí iría tu lógica
    try:
        archivos = os.listdir(SECRETS_DIR)
        if archivos:
            print(f" -> Encontrados: {archivos}")
            # Simular que creamos un log en la salida
            with open(f"{CONFIG_DIR}/log.txt", "a") as f:
                f.write(f"Procesado a las {time.strftime('%H:%M:%S')}\n")
        else:
            print(" -> Carpeta vacía.")
    except Exception as e:
        print(f"Error accediendo a carpetas: {e}")

if __name__ == "__main__":
    print("Iniciando bot...")
    
    # Ejecutamos la primera vez nada más arrancar (opcional, pero recomendado)
    try:
        while True:
            tarea_youtube()
            print(f"Durmiendo durante {INTERVAL} horas...")
            time.sleep(INTERVAL_SECONDS)
        
    except KeyboardInterrupt:
        print("Bot detenido por el usuario.")
        sys.exit(0)
    