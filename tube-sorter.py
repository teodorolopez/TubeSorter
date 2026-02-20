import os
import time
import sys
import pickle
import json
import sqlite3
from pathlib import Path
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.errors import HttpError

CHECK_CHANNELS_EVERY_HOURS = float(os.getenv('CHECK_CHANNELS_EVERY_HOURS', '24'))
SECRETS_DIR = Path(os.getenv('SECRETS_DIR', '/app/secrets'))
CONFIG_DIR = Path(os.getenv('CONFIG_DIR', '/app/config'))

GOOGLE_API_KEY_FILE = SECRETS_DIR / "client_secret.json"
TOKEN_FILE = SECRETS_DIR / "token.pickle"
CONFIG_FILE = CONFIG_DIR / "config.json"  
HISTORY_FILE = CONFIG_DIR / "history.db"

SCOPES = ['https://www.googleapis.com/auth/youtube']
API_SERVICE_NAME = 'youtube'
API_VERSION = 'v3'

NUMBER_OF_VIDEOS_TO_PROCESS = int(os.getenv('NUMBER_OF_VIDEOS_TO_PROCESS', '5'))

class QuotaExceededError(Exception):
    """Excepción personalizada para indicar que se ha excedido la cuota de la API de YouTube."""
    pass

def authenticate_youtube():
    creds = None

    # Intentar cargar el token existente
    if TOKEN_FILE.exists():
        try:
            with TOKEN_FILE.open('rb') as token:
                creds = pickle.load(token)
        except Exception as e:
            print(f"--- [AVISO] El archivo token.pickle está corrupto ({e}). Se requiere nuevo login. ---")
            creds = None # Forzamos el flujo de nuevo login

    # Si no hay credenciales o no son válidas
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("--- [INFO] Refrescando token caducado... ---")
            creds.refresh(Request())
        else:
            print("--- [INFO] Solicitando nueva autorización en el navegador... ---")
            flow = InstalledAppFlow.from_client_secrets_file(
                GOOGLE_API_KEY_FILE, SCOPES)
            creds = flow.run_local_server(port=0)

        # Guardar las credenciales actualizadas
        with TOKEN_FILE.open('wb') as token:
            pickle.dump(creds, token)
            print("--- [OK] Nuevo token guardado correctamente. ---")

    # Devolver el servicio construido
    return build(API_SERVICE_NAME, API_VERSION, credentials=creds)

def initial_config_check():    
    print("--- [INFO] Iniciando validación del entorno ---")

    # 1. Verificar directorios base
    for directory in [SECRETS_DIR, CONFIG_DIR]:
        if not directory.exists():
            print(f"ERROR CRÍTICO: El directorio '{directory}' no existe.")
            sys.exit(1)

    # 2. Verificar configuración principal de la app
    if not CONFIG_FILE.exists():
        print(f"ERROR CRÍTICO: No se encontró el archivo de configuración en {CONFIG_FILE}")
        sys.exit(1)

    # 3. Verificar credenciales maestras de Google
    if not GOOGLE_API_KEY_FILE.exists():
        print(f"ERROR CRÍTICO: Faltan las credenciales de la API en {GOOGLE_API_KEY_FILE}")
        print("Asegúrate de haber descargado el archivo OAuth 2.0 Client IDs de Google Cloud.")
        sys.exit(1)

    print("--- [OK] Chequeo inicial completado con éxito ---")

def init_history_db():
    with sqlite3.connect(HISTORY_FILE) as conn:
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS history (
                video_id TEXT,
                channel_id TEXT,
                playlist_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (video_id, playlist_id)
            )
        ''')

def save_to_history(video_id, channel_id, playlist_id):
    try:
        with sqlite3.connect(HISTORY_FILE) as conn:
            c = conn.cursor()
            c.execute('''
                INSERT INTO history (video_id, channel_id, playlist_id) 
                VALUES (?, ?, ?)
            ''', (video_id, channel_id, playlist_id))
    except sqlite3.IntegrityError:
        print(f" -> El video {video_id} ya existe en el historial para la playlist {playlist_id}.")

def has_been_processed(video_id, playlist_id):
    with sqlite3.connect(HISTORY_FILE) as conn:
        c = conn.cursor()
        c.execute('''
            SELECT 1 FROM history 
            WHERE video_id = ? AND playlist_id = ?
        ''', (video_id, playlist_id))
        result = c.fetchone()
        return result is not None

def load_config():
    with CONFIG_FILE.open('r') as f:
        return json.load(f)

def get_channel_upload_playlist(youtube, channel_id):
    request = youtube.channels().list(
        part="contentDetails",
        id=channel_id
    )
    response = request.execute()
    if 'items' in response and len(response['items']) > 0:
        return response['items'][0]['contentDetails']['relatedPlaylists']['uploads']
    return None

def get_videos_from_playlist(youtube, playlist_id):
    videos = []
    try:
        request = youtube.playlistItems().list(
            part="snippet",
            playlistId=playlist_id,
            maxResults=NUMBER_OF_VIDEOS_TO_PROCESS
        )
        response = request.execute()
        
        for item in response.get('items', []):
            video_id = item['snippet']['resourceId']['videoId']
            channel_id = item['snippet']['channelId']
            videos.append((video_id, channel_id))
            
    except Exception as e:
        # Usamos print aquí, pero si más adelante implementas logging, lo cambias
        print(f"    ❌ Error de la API leyendo videos de la playlist {playlist_id}: {e}")
        
    return videos

def add_video_to_playlist(youtube, video_id, target_playlist_id):
    request = youtube.playlistItems().insert(
        part="snippet",
        body={
            "snippet": {
                "playlistId": target_playlist_id,
                "resourceId": {
                    "kind": "youtube#video",
                    "videoId": video_id
                }
            }
        }
    )
    response = request.execute()
    return response

def sync_playlists(youtube, config_data):
    print(f"\n[{time.strftime('%H:%M:%S')}] Iniciando ciclo de revisión de canales...")

    try:
        for playlist_info in config_data.get('playlists', []):

            # Comprobar si la playlist está activa
            if not playlist_info.get('active', True):
                print(f" Saltando playlist inactiva: {playlist_info.get('name', 'Desconocida')}")
                continue

            target_playlist_id = playlist_info['playlist_id']
            print(f"\n Procesando Playlist Objetivo: {playlist_info['name']}")

            for channel in playlist_info.get('channels', []):
                
                if not channel.get('active', True):
                    print(f"  ⏭️ Saltando canal inactivo: {channel.get('name', 'Desconocido')}")
                    continue
                    
                print(f"  📺 Revisando canal: {channel['name']}")

                try:
                    # Paso A: Obtener el ID de la lista "Uploads" del canal
                    uploads_playlist_id = get_channel_upload_playlist(youtube, channel['id'])
                    if not uploads_playlist_id:
                        print(f"    ⚠️ No se encontró la lista de subidas para {channel['name']}")
                        continue
                        
                    # Paso B: Obtener los últimos N videos (determinado por NUMBER_OF_VIDEOS_TO_PROCESS)
                    videos = get_videos_from_playlist(youtube, uploads_playlist_id)
                    
                    # Paso C: Comprobar la BD y añadir si es nuevo
                    nuevos_añadidos = 0
                    for video_id, channel_id in videos:
                        # Usamos tu base de datos SQLite para validar
                        if not has_been_processed(video_id, target_playlist_id):
                            print(f"    ➕ Añadiendo nuevo video ({video_id}) a la playlist...")
                            add_video_to_playlist(youtube, video_id, target_playlist_id)
                            save_to_history(video_id, channel_id, target_playlist_id)
                            nuevos_añadidos += 1
                            
                    if nuevos_añadidos == 0:
                        print("    ✔️ Sin videos nuevos.")
                        
                except HttpError as e:
                    # Verificar si es error de cuota
                    if e.resp.status in [403, 429] and 'quotaExceeded' in str(e):
                        print(f"\n[🛑 CRÍTICO] Cuota de API agotada. Abortando ciclo actual.")
                        raise QuotaExceededError("Cuota agotada")
                    else:
                        print(f"    ❌ Error de API en canal {channel['name']}: {e}")

                except Exception as e:
                    print(f"    ❌ Error procesando el canal {channel['name']}: {e}")

    except QuotaExceededError:
        # Aquí capturamos el error que lanzamos arriba para salir de los bucles anidados
        print("Reintentando en el próximo ciclo programado...")

    print(f"\n[{time.strftime('%H:%M:%S')}] Ciclo completado.")


def main():
    # Comprobar que lo crítico existe (carpetas, json, claves de google)
    initial_config_check()

    # Inicializar la base de datos (crear archivo y tablas si no existen)
    init_history_db()

    # Autenticarse
    youtube = authenticate_youtube()

    config_data = load_config()

    # Flujo principal: Ejecutar la tarea cada X horas
    try:
        while True:
            sync_playlists(youtube, config_data)

            print(f"Waiting {CHECK_CHANNELS_EVERY_HOURS} hours for the next update check...")
            time.sleep(CHECK_CHANNELS_EVERY_HOURS * 3600)
        
    except KeyboardInterrupt:
        print("Bot detenido por el usuario.")
        sys.exit(0)


if __name__ == "__main__":
    main()
    