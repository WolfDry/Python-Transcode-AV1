"""Module for transcoding audio streams in a video file to AAC format using ffmpeg."""

import json
import os
import subprocess
import sys
from utils import AudioStream, AudioTrack

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
        # Français
        "fr": "Français",
        "fre": "Français",
        "fra": "Français",

        # Anglais
        "en": "Anglais",
        "eng": "Anglais",

        # Espagnol
        "es": "Espagnol",
        "spa": "Espagnol",

        # Allemand
        "de": "Allemand",
        "ger": "Allemand",
        "deu": "Allemand",

        # Italien
        "it": "Italien",
        "ita": "Italien",

        # Portugais
        "pt": "Portugais",
        "por": "Portugais",

        # Néerlandais
        "nl": "Néerlandais",
        "dut": "Néerlandais",
        "nld": "Néerlandais",

        # Chinois
        "zh": "Chinois",
        "chi": "Chinois",
        "zho": "Chinois",

        # Japonais
        "ja": "Japonais",
        "jpn": "Japonais",

        # Russe
        "ru": "Russe",
        "rus": "Russe",

        # Arabe
        "ar": "Arabe",
        "ara": "Arabe",

        # Polonais
        "pl": "Polonais",
        "pol": "Polonais",

        # Turc
        "tr": "Turc",
        "tur": "Turc",

        # Coréen
        "ko": "Coréen",
        "kor": "Coréen",
    }

    return languages.get(code, "Inconnu")

def verif_audio(title, index, log) -> bool:
    """Function to verify if the audio track should be removed based on its title.

    Args:
        title (str): title of the audio track
        index (int): index of the audio track
        log (function): logging function

    Returns:
        bool: True if the audio track should be removed, False otherwise
    """
    name = ""
    if "vfq" in title.lower():
        name += "québécoise"
    if "ad" in title.lower():
        name += "audio descriptive"
    if name != "":
        log(f"La piste audio {index} {title} a été détécté comme {name}", "WARN")
        response = input("Voulez vous supprimer cette piste ❓ (y/n)").strip().lower()
        if response == "y":
            log(f"La piste audio {index} {title} sera supprimée")
            return True
        else:
            log(f"La piste audio {index} {title} est gardée")
            return False
    return False

def get_audio_info(video_path, log) -> list[AudioStream]:
    """ Function to get audio stream information from a video file using ffprobe.

    Args:
        video_path (str): path to the video file
        log (function): logging function

    Raises:
        FileNotFoundError: _if the video file does not exist
        Exception: _if there is an error reading the audio streams

    Returns:
        list[AudioStream]: list of audio streams in the video file
    """
    if not os.path.isfile(video_path):
        raise FileNotFoundError(f"Fichier vidéo non trouvé : {video_path}")
    command = [
        "ffprobe",
        "-v", "error",
        "-select_streams", "a",
        "-show_entries", "stream=index,codec_name,channels,channel_layout,bit_rate:stream_tags=language,title",
        "-of", "json",
        video_path
    ]
    try:
        res = subprocess.run(command, capture_output=True, text=True, check=True)
        data = json.loads(res.stdout)
        audios: list[AudioTrack] = [AudioTrack.from_dict(d) for d in data.get("streams")]
        log(f"{len(audios)} piste(s) audio détectée(s)")
        command_data: list[AudioStream] = []
        for audio in audios:
            is_aac = False
            new_title = get_language_name(audio.tags.language)
            verification_audio = verif_audio(audio.tags.title, audio.index, log)
            if verification_audio:
                continue
            if audio.codec_name == "aac":
                is_aac = True
                log(f"La piste audio {audio.tags.title} sera copiée car elle est déjà en aac", "WARN")
            bitrate = "192k"
            match audio.channels:
                case 2: bitrate = "192k"
                case 6: bitrate = "512k"
                case 8: bitrate = "640k"
            command_data.append(
                AudioStream(
                    index=audio.index,
                    channels=audio.channels,
                    bitrate=bitrate,
                    is_aac=is_aac,
                    title=new_title,
                    lang=audio.tags.language
                )
            )

        return command_data
    except subprocess.CalledProcessError as e:
        stderr = e.stderr.decode('utf-8')
        sys.stderr.write((f"Error: {e}:\n{stderr}\n"))
        sys.exit(-1)


def transcode_audio(video_path, output_path, log):
    """ function to transcode audio streams of a video file to AAC format using ffmpeg.

    Args:
        video_path (str): path to the video file
        output_path (str): path to the output file
        log (function): logging function

    Raises:
        FileNotFoundError: _if the video file does not exist

    Returns:
        bool: True if the transcoding was successful, False otherwise
    """
    if not os.path.isfile(video_path):
        raise FileNotFoundError(f"Fichier vidéo non trouvé : {video_path}")
    audio_stream = get_audio_info(video_path, log)

    command = [
        "ffmpeg",
        "-i", video_path,
        "-map", "0:v",
        "-c:v", "copy",
    ]

    index_out = 0
    for audio in audio_stream:

        command += ["-map", f"0:{audio.index}"]

        if audio.is_aac:
            command += [f"-c:a:{index_out}", "copy"]
        else:
            command += [
                f"-c:a:{index_out}", "aac",
                f"-b:a:{index_out}", audio.bitrate,
                f"-ac:a:{index_out}", str(audio.channels),
                f"-metadata:s:a:{index_out}", f"language={audio.lang}",
                f"-metadata:s:a:{index_out}", f"title={audio.title}",
            ]

        index_out += 1

    command += [
        "-map", "0:s?",
        "-c:s", "copy",
        "-map", "0:t?",
        "-map_metadata", "0"
    ]
    command += [output_path]

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
        log("✅ Transcode audio ok", "OK")
    else:
        result = False
        log(f"❌ Échec pour le transcode audio (code retour {ret})", "ERROR")
    return result
