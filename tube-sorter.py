import os
import time
import sys
from config import *

def initial_config_check():
    print("Intial configuration check:")
    print(f" -> CHECK_CHANNELS_EVERY_HOURS: {CHECK_CHANNELS_EVERY_HOURS}")
    print(f" -> SECRETS_DIR: {SECRETS_DIR}")
    print(f" -> CONFIG_DIR: {CONFIG_DIR}")
    
    # Verificar que las carpetas existen
    if not SECRETS_DIR.exists():
        print(f"Error: SECRETS_DIR '{SECRETS_DIR}' not found.")
        sys.exit(1)
    if not CONFIG_DIR.exists():
        print(f"Error: CONFIG_DIR '{CONFIG_DIR}' not found.")
        sys.exit(1)

    if not GOOGLE_API_KEY_FILE.exists():
        print(f"ERROR CRÍTICO: No se encontró el archivo {GOOGLE_API_KEY_FILE}")
        youtube_oauth()

    if not TOKEN_FILE.exists():
        print(f"ERROR CRÍTICO: No se encontró el archivo {TOKEN_FILE}")
        youtube_oauth()  # Simular autenticación para crear el token

    if not CONFIG_FILE.exists():
        print(f"ERROR CRÍTICO: No se encontró el archivo {CONFIG_FILE}")
        sys.exit(1)

    print("Chequeo inicial completado.")

def youtube_oauth():
    print("Simulando autenticación OAuth con YouTube...")
    # Aquí iría tu lógica de autenticación
    time.sleep(1)  # Simular tiempo de autenticación
    print("Autenticación simulada completada.")

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
    print("Iniciando...")
    initial_config_check()
    
    try:
        while True:
            tarea_youtube()
            print(f"Waiting {CHECK_CHANNELS_EVERY_HOURS} hours for the next update check...")
            time.sleep(CHECK_CHANNELS_EVERY_HOURS * 3600)
        
    except KeyboardInterrupt:
        print("Bot detenido por el usuario.")
        sys.exit(0)