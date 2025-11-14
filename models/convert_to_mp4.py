"""Convert a video file to MP4 format using ffmpeg.

Raises:
    FileNotFoundError: file not found

Returns:
    bool: result of the conversion
"""

import os
import subprocess
import sys
import json

def get_language_name(code: str) -> str:
    """
    Return the full french name of the language from a short code (2 or 3 letters).
    Exemple : 'fr' -> 'Français', 'eng' -> 'Anglais'

    Args:
        code (str): language code

    Returns:
        str: full french name of the language
    """
    code = code.strip().lower()

    languages = {
        # French
        "fr": "Français",
        "fre": "Français",
        "fra": "Français",

        # English
        "en": "Anglais",
        "eng": "Anglais",

        # Spanish
        "es": "Espagnol",
        "spa": "Espagnol",

        # German
        "de": "Allemand",
        "ger": "Allemand",
        "deu": "Allemand",

        # Italian
        "it": "Italien",
        "ita": "Italien",

        # Portuguese
        "pt": "Portugais",
        "por": "Portugais",

        # Dutch
        "nl": "Néerlandais",
        "dut": "Néerlandais",
        "nld": "Néerlandais",

        # Chinese
        "zh": "Chinois",
        "chi": "Chinois",
        "zho": "Chinois",

        # Japanese
        "ja": "Japonais",
        "jpn": "Japonais",

        # Russian
        "ru": "Russe",
        "rus": "Russe",

        # Arabic
        "ar": "Arabe",
        "ara": "Arabe",

        # Polish
        "pl": "Polonais",
        "pol": "Polonais",

        # Turkish
        "tr": "Turc",
        "tur": "Turc",

        # Korean
        "ko": "Coréen",
        "kor": "Coréen",
    }

    return languages.get(code, "Unknown")

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

def get_subtitle_data(subtitle):
    """ Get subtitle data from a subtitle stream.

    Args:
        subtitle (dict): subtitle stream data
    Returns:
        dict: subtitle data
    """
    codec = subtitle.get("codec_name", "unknown")
    index = subtitle["index"]
    lang_code = subtitle.get("tags", {}).get("language", "und")
    title = get_language_name(lang_code)
    return {
        "codec": codec,
        "index": index,
        "lang": lang_code,
        "title": title
    }

def convert_to_mp4(video_path, temp_path, log):
    """ Convert a video file to MP4 format using ffmpeg.

    Args:
        video_path (str): path to the video file
        temp_path (str): temporary path to the video file in conversion
        log (function): logging function

    Raises:
        FileNotFoundError: _if the video file does not exist
        NotADirectoryError: _if the temporary path does not exist

    Returns:
        bool: result of the conversion
    """
    if not os.path.isfile(video_path):
        raise FileNotFoundError(f"Fichier vidéo non trouvé : {video_path}")
    if not os.path.isdir(temp_path):
        raise NotADirectoryError(f"Dossier temporaire non trouvé : {temp_path}")

    file_name = os.path.basename(video_path).rsplit('.', 1)[0]

    subtitles = get_subtitles(video_path, log)

    command = [
        "ffmpeg",
        "-i", video_path,
        "-map", "0:v",
        "-c:v", "copy",
        "-map", "0:a",
        "-c:a", "copy",
    ]

    index_out = 0
    for subtitle in subtitles:
        subtitle_data = get_subtitle_data(subtitle)
        if subtitle_data["codec"] not in {"subrip", "ass", "ssa", "text"}:
            log(f"Piste #{subtitle_data['index']} ({subtitle_data['lang']}) de type {subtitle_data['codec']} est ignorée", "WARN")
            continue
        command += [
            "-map", f"0:{subtitle_data['index']}",
            f"-metadata:s:s:{index_out}", f"title={subtitle_data['title']}",
            f"-metadata:s:s:{index_out}", f"language={subtitle_data['lang']}",
        ]
        index_out += 1

    command += [
        "-c:s", "mov_text",
        "-map_metadata", "0",
        "-map_chapters", "0",
        "-movflags", "use_metadata_tags+faststart",
        f"{temp_path}\\{file_name}.mp4"
    ]

    # process = subprocess.Popen(
    #     command,
    #     stdout=subprocess.PIPE,
    #     stderr=subprocess.STDOUT,
    #     text=True,
    #     bufsize=1
    # )

    # for line in process.stdout:
    #     if "frame=" in line or "time=" in line or "Subtitle" in line:
    #         log(line, "INFO")
    # result = False

    # ret = process.wait()
    # if ret == 0:
    #     result = True
    #     log("✅ Conversion en mp4 ok", "OK")
    # else:
    #     result = False
    #     log(f"❌ Échec pour le transcode audio (code retour {ret})", "ERROR")
    # return result
