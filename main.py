"""Main script to transcode audio, convert to MP4, and transcode video to AV1."""
import sys
import os
import shutil
from datetime import datetime
from dotenv import load_dotenv
from models.transcode_audio import transcode_audio
from models.convert_to_mp4 import convert_to_mp4
from models.transcode_av1 import transcode_video

load_dotenv()

# Chargement et validation des variables d'environnement
OUTPUT_PATH = os.getenv("OUTPUT_PATH")
TEMP_PATH = os.getenv("TEMP_PATH")

if not OUTPUT_PATH or not TEMP_PATH:
    raise ValueError("Les variables d'environnement OUTPUT_PATH et TEMP_PATH doivent être définies")

if not os.path.isdir(OUTPUT_PATH):
    raise NotADirectoryError(f"Le répertoire de sortie n'existe pas : {OUTPUT_PATH}")

if not os.path.isdir(TEMP_PATH):
    raise NotADirectoryError(f"Le répertoire temporaire n'existe pas : {TEMP_PATH}")

def log(msg: str, level="INFO"):
    """Function to log messages with different severity levels.

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

def move_file(src: str, dest: str) -> bool:
    """Move a file from src to dest.

    Args:
        src (str): source file path
        dest (str): destination file path
    Returns:
        bool: True if the file was moved successfully, False otherwise
    """
    log(f"Déplacement du fichier {src}", "INFO")
    try:
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        shutil.move(src, dest)
        log(f"Fichier déplacé de {src} à {dest}.", "OK")
        return True
    except (OSError, shutil.Error) as e:
        log(f"Erreur lors du déplacement du fichier de {src} à {dest} : {e}", "ERROR")
        return False

def cleanup_temp_files(temp_file: str):
    """Remove temporary files if they exist.

    Args:
        temp_file (str): path to temporary file to remove
    """
    try:
        if os.path.isfile(temp_file):
            os.remove(temp_file)
            log(f"Fichier temporaire supprimé : {temp_file}", "INFO")
    except OSError as e:
        log(f"Erreur lors de la suppression du fichier temporaire : {e}", "WARN")

def process_video(input_file: str, base_filename: str, final_output_path: str) -> bool:
    """Process a single video through the complete transcode pipeline.

    Args:
        input_file (str): path to input video file
        output_filename (str): filename without extension for output
        final_output_path (str): final destination directory

    Returns:
        bool: True if all steps succeeded, False otherwise
    """
    output_mp4_filename = f"{base_filename}.mp4"
    temp_mp4_path = os.path.join(TEMP_PATH, output_mp4_filename)
    temp_audio_path = os.path.join(TEMP_PATH, f"audio_{output_mp4_filename}")
    temp_final_path = os.path.join(TEMP_PATH, f"final_{output_mp4_filename}")
    final_mp4_path = os.path.join(final_output_path, output_mp4_filename)

    try:
        # Étape 1 : Conversion en MP4
        log("[Étape 1/3] Conversion en MP4...", "INFO")
        mp4_result = convert_to_mp4(input_file, TEMP_PATH, log)
        if not mp4_result["success"]:
            log("❌ Conversion en MP4 échouée", "ERROR")
            return False

        if not move_file(mp4_result["output"], temp_mp4_path):
            log("❌ Déplacement du fichier MP4 échoué", "ERROR")
            return False

        log("✅ Conversion en MP4 terminée.", "OK")

        # Étape 2 : Transcodage audio
        log("[Étape 2/3] Transcodage audio...", "INFO")
        if not transcode_audio(temp_mp4_path, temp_audio_path, log):
            log("❌ Transcodage audio échoué", "ERROR")
            cleanup_temp_files(temp_mp4_path)
            return False

        # Remplacer le fichier MP4 par la version avec audio transcodé
        if not move_file(temp_audio_path, temp_mp4_path):
            log("❌ Remplacement du fichier audio échoué", "ERROR")
            cleanup_temp_files(temp_mp4_path)
            cleanup_temp_files(temp_audio_path)
            return False

        log("✅ Transcodage audio terminé.", "OK")

        # Étape 3 : Transcodage vidéo AV1
        log("[Étape 3/3] Transcodage vidéo AV1...", "INFO")
        if not transcode_video(temp_mp4_path, temp_final_path, log):
            log("❌ Transcodage vidéo AV1 échoué", "ERROR")
            cleanup_temp_files(temp_mp4_path)
            return False

        # Déplacer le fichier final vers OUTPUT_PATH
        if not move_file(temp_final_path, final_mp4_path):
            log("❌ Déplacement du fichier final échoué", "ERROR")
            cleanup_temp_files(temp_mp4_path)
            cleanup_temp_files(temp_final_path)
            return False

        log("✅ Transcodage vidéo AV1 terminé.", "OK")

        # Nettoyage
        cleanup_temp_files(temp_mp4_path)
        log(f"✅ Fichier final sauvegardé : {final_mp4_path}", "OK")
        return True

    except (OSError, ValueError, RuntimeError) as e:
        log(f"❌ Erreur lors du traitement du fichier : {e}", "ERROR")
        cleanup_temp_files(temp_mp4_path)
        cleanup_temp_files(temp_audio_path)
        cleanup_temp_files(temp_final_path)
        return False

# Point d'entrée principal
if __name__ == "__main__":
    directory = input("Entrez le répertoire contenant les fichiers vidéo à traiter : ").strip()

    if not os.path.isdir(directory):
        log(f"❌ Le répertoire n'existe pas : {directory}", "ERROR")
        sys.exit(1)

    video_files = [f for f in os.listdir(directory) if f.lower().endswith(('.mp4', '.mkv', '.avi', '.mov'))]

    if not video_files:
        log(f"❌ Aucun fichier vidéo trouvé dans {directory}", "ERROR")
        sys.exit(1)

    log(f"{len(video_files)} fichier(s) vidéo trouvé(s) dans le répertoire {directory}.", "INFO")

    processed_count = 0
    for video_file in video_files:
        input_path = os.path.join(directory, video_file)
        output_filename = os.path.splitext(video_file)[0]

        log(f"\n{'='*60}", "INFO")
        log(f"Traitement du fichier : {video_file}", "INFO")
        log(f"{'='*60}", "INFO")

        if process_video(input_path, output_filename, OUTPUT_PATH):
            processed_count += 1

        log("", "INFO")

    log(f"{'='*60}", "INFO")
    log(f"Traitement terminé : {processed_count}/{len(video_files)} fichier(s) traité(s) avec succès.", "OK")
    log(f"{'='*60}", "INFO")
