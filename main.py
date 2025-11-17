"""Main script to transcode audio, convert to MP4, and transcode video to AV1."""
import sys
import os
from datetime import datetime
from dotenv import load_dotenv
from models.transcode_audio import transcode_audio as audio
from models.convert_to_mp4 import convert_to_mp4 as mp4
from models.transcode_av1 import transcode_video as video

load_dotenv()

OUTPUT_PATH =os.getenv("OUTPUT_PATH")
temp_path =os.getenv("TEMP_PATH")
video_path =os.getenv("VIDEO_PATH")

def log(msg: str, level="INFO"):
    """function to log messages with different severity levels.

    Args:
        msg (str): message to log
        level (str, optional): Defaults to "INFO". Possible values: "ERROR", "OK", "WARN", "INFO".
    """
    color = {
        "ERROR": "\033[91m",    # rouge
        "OK": "\033[92m",      # vert
        "WARN": "\033[93m",    # jaune
        "INFO": "\033[94m",    # bleu
    }.get(level, "")
    reset = "\033[0m"
    print(f"{color}[{level}] {datetime.now().strftime('%H:%M:%S')} | {msg}{reset}")
    sys.stdout.flush()

def move_file(src: str, dest: str) -> bool:
    """Move a file from src to dest.

    Args:
        src (str): source file path
        dest (str): destination file path
    Returns:
        bool: True if the file was moved successfully, False otherwise
    """
    log(f"Déplacement du fichier {src}", "INFO")
    try:
        os.replace(src, dest)
        log(f"Fichier déplacé de {src} à {dest}.", "OK")
        return True
    except Exception as e:
        log(f"Erreur lors du déplacement du fichier de {src} à {dest} : {e}", "ERROR")
        return False

result = mp4(video_path, temp_path, log)
if result["success"]:
    if move_file(result["output"], os.path.join(OUTPUT_PATH, result["file_name"])):
        log("Conversion en MP4 terminée avec succès.", "OK")
        video_path = os.path.join(OUTPUT_PATH, result["file_name"])
        temp_path = os.path.join(temp_path, result["file_name"])
        audio(video_path, temp_path, log)
    #     if RESULT:
    #         log("Transcodage audio terminée avec succès.", "OK")
    #         RESULT = video(VIDEO_PATH, OUTPUT_PATH, log)
    #         if RESULT:
    #             log("Transcodage vidéo AV1 terminé avec succès.", "OK")
    #         else:
    #             log("Échec du transcodage vidéo AV1.", "ERROR")
    #     else:
    #         log("Échec du transcodage audio.", "ERROR")
# else:
#     log("Échec de la conversion en MP4.", "ERROR")

print(f"RESULT : {result}")
