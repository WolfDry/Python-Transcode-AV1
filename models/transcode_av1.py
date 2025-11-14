"""Transcode a video file to AV1 format using NVIDIA NVENC."""

from fractions import Fraction
import json
import os
import subprocess
import sys
from utils import VideoTrack, TranscodeData

def classify_resolution(width: int, height: int) -> str:
    """ Classify video resolution based on width and height.

    Args:
        width (int): width of the video
        height (int): height of the video

    Returns:
        str: resolution classification (e.g., "1080p", "720p", etc.)
    """

    if not width or not height:
        return "Unknown"

    ratio = width / height

    if ratio > 2.0:
        # Widescreen ultra large format
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
        # Standard formats
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
    """ Get resolution parameters based on resolution classification.

    Args:
        resolution (str): resolution classification

    Returns:
        object: resolution parameters
    """
    if resolution == "2160p":
        return {
            "cq": 27,
            "tile_columns": 2
        }
    if resolution == "1440p":
        return {
            "cq": 29,
            "tile_columns": 1
        }
    if resolution == "1080p":
        return {
            "cq": 31,
            "tile_columns": 1
        }
    return {
        "cq": 33,
        "tile_columns": 1,
    }

def get_framerate(framerate, avg):
    """ Get framerate value as float from framerate string or average framerate.

    Args:
        framerate (int): framerate of the video
        avg (int): average framerate of the video

    Returns:
        float: framerate value
    """
    val = framerate if framerate and framerate != "0/0" else avg
    try:
        return float(Fraction(val))
    except (ZeroDivisionError, ValueError):
        return 24.0

def detect_hdr(info) -> bool:
    """ Detect if the video track is HDR based on its metadata.

    Args:
        info (VideoTrack): video track info

    Returns:
        bool: True if HDR detected, False otherwise
    """
    trc = (info.color_transfer or "").lower()
    prim = (info.color_primaries or "").lower()
    csp  = (info.color_space or "").lower()
    mdl  = info.mastering_display_metadata
    cll  = info.content_light_metadata
    sdl  = info.side_data_list or []
    has_mdl = bool(mdl) or any(d.get("side_data_type","").lower().startswith("mastering") for d in sdl)
    has_cll = bool(cll) or any(d.get("side_data_type","").lower().startswith("content light") for d in sdl)

    return (trc in ["smpte2084","arib-std-b67"]) or (prim=="bt2020") or (csp=="bt2020nc") or has_mdl or has_cll

def pick_params_from_source(info):
    """_summary_

    Args:
        info ({
            resolution (str): resolution classification    
            is_hdr (bool): HDR status
            bitrate (int): source bitrate in bps
        }): video track info

    Returns:
        _dict_: transcoding parameters
    """
    res = info['resolution']
    is_hdr = info['is_hdr']

    # 1) Bitrate source (bps)
    src_br = int(info.get('bitrate'))

    # 2) ratio de réduction cible selon résolution & nature
    if res == "2160p":
        ratio_min = 0.60
    elif res == "1440p":
        ratio_min = 0.50
    elif res == "1080p":
        ratio_min = 0.45
    else:  # 720p et dessous
        ratio_min = 0.40

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
    """ Get transcoding information from the video file.

    Args:
        video_path (srt): path to the video file

    Raises:
        FileNotFoundError: _if the video file does not exist
        Exception: _if no video track is found

    Returns:
        TranscodeData: transcoding data
    """
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

    res = subprocess.run(command, capture_output=True, text=True, check=True)
    infos = json.loads(res.stdout)
    if not infos.get("streams"):
        raise RuntimeError("Aucune piste vidéo trouvée")
    duration = float(infos.get("format").get("duration"))
    infos: VideoTrack = VideoTrack.from_dict(infos.get("streams")[0])
    resolution = classify_resolution(infos.width, infos.height)
    resolution_param = get_resolution_param(resolution)
    framerate = get_framerate(infos.r_frame_rate, infos.avg_frame_rate)

    is_hdr = detect_hdr(infos)
    data = {
        "pix_fmt": infos.pix_fmt,
        "color_primaries": infos.color_primaries,
        "color_transfer": infos.color_transfer,
        "mastering_display_metadata": infos.mastering_display_metadata,
        "is_hdr": is_hdr,
        "resolution": resolution,
        "framerate": framerate,
        "cq": resolution_param["cq"],
        "tile_columns": resolution_param["tile_columns"],
        "bitrate": infos.bit_rate or int(size * 8 / duration),
        "duration": duration,
    }
    data |= pick_params_from_source(data)
    return data

def transcode_video(video_path, output_path, log):
    """_summary_

    Args:
        video_path (str): path to the video file
        output_path (str): path to save the transcoded video
        log (function): logging function

    Raises:
        FileNotFoundError: _if the video file does not exist

    Returns:
        bool: True if transcoding is successful, False otherwise
    """
    if not os.path.isfile(video_path):
        raise FileNotFoundError(f"Fichier vidéo non trouvé : {video_path}")

    info: TranscodeData = TranscodeData(**get_info(video_path))

    pix_fmt_out = "yuv420p10le" if info.is_hdr else "yuv420p"
    primaries, trc, cspace = (
        ("bt2020","smpte2084","bt2020nc") if info.is_hdr else
        ("bt709","bt709","bt709")
    )
    gop = str(int(round(2 * info.framerate)))
    tiles = str(info.tile_columns)
    cq = str(info.cq)
    b_v = str(info.b_v)
    maxrate = str(info.maxrate)
    bufsize = str(info.bufsize)

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
        log("✅ Transcode vidéo ok", "OK")
    else:
        result = False
        log(f"❌ Échec pour le transcode vidéo (code retour {ret})", "ERROR")

    return result
