@echo off
REM Script de démarrage rapide pour Python-Transcode-AV1

REM Vérifier si l'environnement virtuel existe
if not exist "venv\" (
    echo Création de l'environnement virtuel...
    python -m venv venv
)

REM Activer l'environnement virtuel
call venv\Scripts\activate.bat

REM Vérifier si les dépendances sont installées
pip show python-dotenv >nul 2>&1
if errorlevel 1 (
    echo Installation des dépendances...
    pip install -r requirements.txt
)

REM Vérifier si le fichier .env existe
if not exist ".env" (
    echo ERREUR: Le fichier .env n'existe pas!
    echo Veuillez créer un fichier .env à partir de .env.example
    echo Exemple: copy .env.example .env
    pause
    exit /b 1
)

REM Vérifier FFmpeg
where ffmpeg >nul 2>&1
if errorlevel 1 (
    echo ERREUR: FFmpeg n'est pas installé ou non accessible dans PATH
    echo Veuillez installer FFmpeg: https://ffmpeg.org/download.html
    pause
    exit /b 1
)

REM Vérifier NVIDIA CUDA
nvidia-smi >nul 2>&1
if errorlevel 1 (
    echo ATTENTION: NVIDIA CUDA n'est pas détecté
    echo Le transcodage AV1 ne sera pas accéléré par GPU
    echo Veuillez installer NVIDIA CUDA: https://developer.nvidia.com/cuda-downloads
)

REM Lancer le script principal
python .\main.py

pause
