from fractions import Fraction
import json, os, subprocess, sys

def classify_resolution(width: int, height: int) -> str:
    """
    Détecte la résolution standard dune vidéo (2160p, 1440p, 1080p, etc.)
    en tenant compte des ratios cinéma (21:9, 2.35:1...).
    """

    if not width or not height:
        return "Unknown"

    ratio = width / height

    # Seuils de ratio
    if ratio > 2.0:
        # Format large (cinémascope) : on se base surtout sur la largeur
        if width >= 3800:
            return "2160p"
        elif width >= 2500:
            return "1440p"
        elif width >= 1900:
            return "1080p"
        elif width >= 1200:
            return "720p"
        else:
            return "480p"
    else:
        # Format classique 16:9 ou plus carré
        if height >= 2000:
            return "2160p"
        elif height >= 1300:
            return "1440p"
        elif height >= 900:
            return "1080p"
        elif height >= 650:
            return "720p"
        elif height >= 400:
            return "480p"
        else:
            return "SD"


def get_resolution_param(resolution):
    if(resolution == "2160p"):
        return {
            "cq": 27,
            "tile_columns": 2
        }
    if(resolution == "1440p"):
        return {
            "cq": 29,
            "tile_columns": 1
        }
    if(resolution == "1080p"):
        return {
            "cq": 31,
            "tile_columns": 1
        }
    return {
        "cq": 33,
        "tile_columns": 1,
    }

def get_framerate(r, avg):
    val = r if r and r != "0/0" else avg
    try:
        return float(Fraction(val))
    except Exception:
        return 24.0

def detect_hdr(info):
    trc = (info.get("color_transfer") or "").lower()
    prim = (info.get("color_primaries") or "").lower()
    csp  = (info.get("color_space") or "").lower()
    mdl  = info.get("mastering_display_metadata")
    cll  = info.get("content_light_metadata")
    sdl  = info.get("side_data_list") or []
    has_mdl = bool(mdl) or any(d.get("side_data_type","").lower().startswith("mastering") for d in sdl)
    has_cll = bool(cll) or any(d.get("side_data_type","").lower().startswith("content light") for d in sdl)

    return (trc in ["smpte2084","arib-std-b67"]) or (prim=="bt2020") or (csp=="bt2020nc") or has_mdl or has_cll

def pick_params_from_source(info):
    """
    info = dict retourné par ton get_info(): 
    { 'resolution': '2160p'|'1440p'|'1080p'|'720p'|..., 
      'fps': float, 'is_hdr': bool,
      'width': int, 'height': int,
      'video_bitrate': int (en bps, optionnel), 
      'duration_sec': float (fallback), 'filesize_bytes': int (fallback) }
    """
    res = info['resolution']
    is_hdr = info['is_hdr']

    # 1) Bitrate source (bps)
    src_br = int(info.get('bitrate'))

    # 2) ratio de réduction cible selon résolution & nature
    if res == "2160p":
        ratio_min, ratio_max = (0.60, 0.70 if is_hdr else 0.65)
    elif res == "1440p":
        ratio_min, ratio_max = (0.50, 0.65)
    elif res == "1080p":
        ratio_min, ratio_max = (0.45, 0.60)
    else:  # 720p et dessous
        ratio_min, ratio_max = (0.40, 0.55)

    target_ratio = ratio_min
    target_br = int(src_br * target_ratio)

    # 3) cq de base selon résolution
    if res == "2160p":
        cq = 26 if is_hdr else 27
        tiles = 2
    elif res == "1440p":
        cq = 29
        tiles = 1
    elif res == "1080p":
        cq = 31
        tiles = 1
    else:
        cq = 33
        tiles = 1

    # Ajuste CQ si on vise un ratio très bas (plus de compression)
    if target_ratio <= 0.48:  # objectif agressif
        cq += 1

    # 4) garde-fous VBR
    maxrate = int(target_br * 1.30)
    bufsize = int(target_br * 2.00)

    return {
        "cq": str(cq),
        "b_v": str(target_br),
        "maxrate": str(maxrate),
        "bufsize": str(bufsize),
        "tile_columns": str(tiles)
    }


def get_info(video_path):
    if not os.path.isfile(video_path):
        raise FileNotFoundError(f"Fichier vidéo non trouvé : {video_path}")
    
    size = os.path.getsize(video_path)
    
    command = [
        "ffprobe", "-v", "error",
        "-select_streams", "v:0",
        "-show_entries",
        "stream=width,height,bit_rate,r_frame_rate,avg_frame_rate,pix_fmt,color_primaries,color_transfer,color_space,mastering_display_metadata,content_light_metadata,side_data_list",
        "-show_entries",
        "format=duration",
        "-of", "json",
        video_path
    ]

    res = subprocess.run(command, capture_output=True, text=True)
    infos = json.loads(res.stdout)
    if not infos.get("streams"):
        raise Exception("Aucune piste vidéo trouvée")
    duration = float(infos.get("format").get("duration"))
    infos = infos.get("streams")[0]
    pix_fmt = infos.get("pix_fmt")
    color_transfer = infos.get("color_transfer")
    color_primaries = infos.get("color_primaries")
    mastering_display_metadata = infos.get("mastering_display_metadata")
    resolution = classify_resolution(infos.get("width"), infos.get("height"))
    resolution_param = get_resolution_param(resolution)
    r_frame_rate = infos.get("r_frame_rate")
    average_framerate = infos.get("avg_frame_rate")
    framerate = get_framerate(r_frame_rate, average_framerate)
    bit_rate = infos.get("bit_rate")

    is_hdr = detect_hdr(infos)
    data = {
        "pix_fmt": pix_fmt,
        "color_primaries": color_primaries,
        "color_transfer": color_transfer,
        "mastering_display_metadata": mastering_display_metadata,
        "is_hdr": is_hdr,
        "resolution": resolution,
        "framerate": framerate,
        "cq": resolution_param["cq"],
        "tile_columns": resolution_param["tile_columns"],
        "bitrate": bit_rate or int(size * 8 / duration),
        "duration": duration,
    }
    data |= pick_params_from_source(data)
    return data

def transcode_video(video_path, output_path, log):
    if not os.path.isfile(video_path):
        raise FileNotFoundError(f"Fichier vidéo non trouvé : {video_path}")

    info = get_info(video_path)

    pix_fmt_out = "yuv420p10le" if info["is_hdr"] else "yuv420p"
    primaries, trc, cspace = (
        ("bt2020","smpte2084","bt2020nc") if info["is_hdr"] else
        ("bt709","bt709","bt709")
    )
    gop = str(int(round(2 * info["framerate"])))
    tiles = str(info["tile_columns"])
    cq = str(info["cq"])
    b_v = str(info["b_v"])
    maxrate = str(info["maxrate"])
    bufsize = str(info["bufsize"])

    # Si dispo dans la source alors on rajoute -mastering_display et -content_light
    command = [
        "ffmpeg",
        "-hwaccel","cuda",
        "-i", video_path,
        "-map","0:v:0","-map","0:a?","-map","0:s?",
        "-pix_fmt", pix_fmt_out,
        "-c:v","av1_nvenc","-preset","p3",
        "-rc","vbr","-b:v", b_v, "-maxrate", maxrate, "-bufsize", bufsize,
        "-cq", cq,
        "-g", gop,"-rc-lookahead","32","-spatial-aq","1","-temporal-aq","1",
        "-tile-columns", tiles,"-tile-rows","1",
        "-color_primaries", primaries,"-color_trc", trc,"-colorspace", cspace,"-color_range","tv",
        "-c:a","copy","-c:s","copy",
        "-movflags", "+faststart",
        "-stats","-stats_period","5","-loglevel","info",
        f"{output_path}"
    ]

    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )

    for line in process.stdout:
        if "frame=" in line or "time=" in line or "Video" in line:
            sys.stdout.write(line)
            sys.stdout.flush()
    
    result = False

    ret = process.wait()
    if ret == 0:
        result = True
        log(f"✅ Transcode vidéo ok", "OK")
    else:
        result = False
        log(f"❌ Échec pour le transcode vidéo (code retour {ret})", "ERROR")
    
    return result