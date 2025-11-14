"""Extract subtitles from a video file using ffmpeg and ffprobe.

Raises:
    FileNotFoundError: _if the video file does not exist
    Exception: _on ffprobe error
    FileExistsError: _if the output path does not exist

Returns:
    bool: result of the extraction
"""

import subprocess
import json
import os
import sys
import re

def sanitize(name: str) -> str:
    """Sanitize a string to be used as a filename by removing invalid characters.

    Args:
        name (str): name to sanitize

    Returns:
        str: sanitized name
    """
    return re.sub(r'[<>:"/\\|?*\n\r\t]', '_', name).strip() or "subtitle"


def get_subtitles(video_path, log):
    """_summary_

    Args:
        video_path (str): path to the video file
        log (function): logging function

    Raises:
        FileNotFoundError: if the video file does not exist
        Exception: on ffprobe error

    Returns:
        bool: True if the extraction was successful, False otherwise
    """
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
        stderr = e.stderr.decode('utf-8')
        sys.stderr.write((f"Error: {e}:\n{stderr}\n"))
        sys.exit(-1)


def extract_subtitles(video_path, output_path, log):
    """ Extract subtitles from a video file using ffmpeg.

    Args:
        video_path (str): path to the video file
        output_path (str): path to save the extracted subtitles
        log (function): logging function

    Raises:
        FileExistsError: _if the output path does not exist

    Returns:
        bool: True if the extraction was successful, False otherwise
    """
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
