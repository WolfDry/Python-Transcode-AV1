import json
import os, subprocess, sys

def get_language_name(code: str) -> str:
    """
    Retourne le nom complet de la langue à partir d'un code abrégé (2 ou 3 lettres).
    Exemple : 'fr' -> 'Français', 'eng' -> 'Anglais'
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


def get_audio_info(video_path, log):
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
        audios = data.get("streams", [])
        log(f"{len(audios)} piste(s) audio détectée(s)")
        
        command_data = []

        for audio in audios:
            index = audio.get("index")
            codec = audio.get("codec_name")
            channels = audio.get("channels")
            tags = audio.get("tags")
            lang = tags.get("language")
            title = tags.get("title")
            is_aac = False
            new_title = get_language_name(lang)

            if codec == "aac":
                is_aac = True
                log(f"La piste audio {title} a été ignoré car elle est déjà en aac", "WARN")
            
            bitrate = "192k"

            match channels:
                case 2: bitrate = "192k"
                case 6: bitrate = "512k"
                case 8: bitrate = "640k"
            
            command_data.append({
                "index": index,
                "channels": channels,
                "bitrate": bitrate,
                "is_aac": is_aac,
                "title": new_title,
                "lang": lang
            })

        return command_data
    
    except subprocess.CalledProcessError as e:
        raise Exception(f"Erreur lors de la lecteur des sous-titres : {e.stderr.decode()}")


def transcode_audio(video_path, output_path, log):
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
        index = audio["index"]
        channels = audio.get("channels", 2)
        bitrate = audio.get("bitrate", "192k")
        is_aac = audio.get("is_aac", False)
        lang = audio.get("lang")
        title = audio.get("title")

        command += ["-map", f"0:{index}"]

        if is_aac:
            command += [f"-c:a:{index_out}", "copy"]
        else:
            command += [
                f"-c:a:{index_out}", "aac",
                f"-b:a:{index_out}", bitrate,
                f"-ac:a:{index_out}", str(channels),
                f"-metadata:s:a:{index_out}", f"language={lang}",
                f"-metadata:s:a:{index_out}", f"title={title}",
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
        log(f"✅ Transcode audio ok", "OK")
    else:
        result = False
        log(f"❌ Échec pour le transcode audio (code retour {ret})", "ERROR")
    
    return result


