import subprocess, json, os, sys, re
from datetime import datetime

def sanitize(name: str) -> str:
    return re.sub(r'[<>:"/\\|?*\n\r\t]', '_', name).strip() or "subtitle"


def get_subtitles(video_path, log):
    if not os.path.isfile(video_path):
        raise FileNotFoundError(f"Fichier vidéo non trouvé : {video_path}")
    
    command = [
        "ffprobe",
        "-v", "error",
        "-select_streams", "s",
        "-show_entries", "stream=index,codec_name,codec_type:stream_tags=language,title",
        "-of", "json",
        video_path
    ]

    try:
        res = subprocess.run(command, capture_output=True, text=True, check=True)
        data = json.loads(res.stdout)
        subtitles = data.get("streams", [])
        log(f"{len(subtitles)} piste(s) de sous-titres détectée(s)")
        return subtitles
    except subprocess.CalledProcessError as e:
        raise Exception(f"Erreur lors de la lecteur des sous-titres : {e.stderr.decode()}")


def extract_subtitles(video_path, output_path, log):
    if not os.path.isdir(output_path):
        raise FileExistsError(f"Fichier vidéo non trouvé : {output_path}")
    
    subtitles = get_subtitles(video_path, log)

    
    for subtitle in subtitles:
        codec = subtitle.get("codec_name", "unknown")
        index = subtitle["index"]
        tags = subtitle.get("tags", {}) or {}
        lang = tags.get("language", "und")
        title = sanitize(tags.get("title", ""))

        if codec != "subrip":
            log(f"Piste #{index} ignorée (codec {codec})", "WARN")
            continue

        output = f"{output_path}{title}.{lang}.srt"

        log(f"→ Extraction piste #{index} ({lang}, {codec}) → {output}")

        command = [
            "ffmpeg",
            "-i", video_path,
            "-map", f"0:{index}",
            "-c:s", "srt",
            output,
            "-y"
        ]


        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )

        for line in process.stdout:
            if "frame=" in line or "time=" in line or "Subtitle" in line:
                sys.stdout.write(line)
                sys.stdout.flush()

        result = False
        
        ret = process.wait()
        if ret == 0:
            result = True
            log(f"✅ Extraction réussie pour la piste #{index}", "OK")
        else:
            result = False
            log(f"❌ Échec pour la piste #{index} (code retour {ret})", "ERROR")
        
    return result

def main(video_path, output_path, log):
    return extract_subtitles(video_path, output_path, log)