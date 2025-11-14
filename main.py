"""Main script to transcode audio, convert to MP4, and transcode video to AV1."""
import sys
import os
from datetime import datetime
from models.transcode_audio import transcode_audio as audio
from models.convert_to_mp4 import convert_to_mp4 as mp4
from models.transcode_av1 import transcode_video as video
from dotenv import load_dotenv

load_dotenv()

VIDEO_PATH =os.getenv("VIDEO_PATH")
OUTPUT_PATH =os.getenv("OUTPUT_PATH")
TEMP_PATH =os.getenv("TEMP_PATH")

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

RESULT = video(VIDEO_PATH, OUTPUT_PATH, log)
# if RESULT:
#     log("Conversion en MP4 terminée avec succès.", "OK")
#     RESULT = audio(VIDEO_PATH, OUTPUT_PATH, log)
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

print(f"RESULT : {RESULT}")
