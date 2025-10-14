import os, subprocess, sys

def convert_to_mp4(video_path, log):
    if not os.path.isfile(video_path):
        raise FileNotFoundError(f"Fichier vidéo non trouvé : {video_path}")
    
    file_folder = os.path.dirname(video_path)
    file_name = os.path.basename(video_path).rsplit('.', 1)[0]

    command = [
        "ffmpeg",
        "-i", video_path,
        "-map", "0:v",
        "-c:v", "copy",
        "-map", "0:a",
        "-c:a", "copy",
        "-map", "0:s?",
        "-c:s", "mov_text",
        "-map_metadata", "0",
        "-movflags", "use_metadata_tags",
        f"{file_folder}\\{file_name}.mp4"
    ]

    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )

    for line in process.stdout:
        if "frame=" in line or "time=" in line or "Audio" in line:
            sys.stdout.write(line)
            sys.stdout.flush()
    
    result = False

    ret = process.wait()
    if ret == 0:
        result = True
        log(f"✅ Transcode audio ok", "OK")
    else:
        result = False
        log(f"❌ Échec pour le transcode audio (code retour {ret})", "ERROR")
    
    return result

