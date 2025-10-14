import os
import sys
from datetime import datetime
from transcode_audio import transcode_audio as audio
from convert_to_mp4 import convert_to_mp4 as mp4
from transcode_av1 import transcode_video as video

def log(msg: str, level="INFO"):
    color = {
        "ERROR": "\033[91m",    # rouge
        "OK": "\033[92m",      # vert
        "WARN": "\033[93m",    # jaune
        "INFO": "\033[94m",    # bleu
    }.get(level, "")
    reset = "\033[0m"
    print(f"{color}[{level}] {datetime.now().strftime('%H:%M:%S')} | {msg}{reset}")
    sys.stdout.flush()

result = video(video_path, output_path, log)

print(f"result : {result}")