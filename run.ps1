# Script de démarrage rapide pour Python-Transcode-AV1 (PowerShell)

# Vérifier si l'environnement virtuel existe
if (!(Test-Path "venv")) {
    Write-Host "Création de l'environnement virtuel..." -ForegroundColor Cyan
    python -m venv venv
}

# Activer l'environnement virtuel
& ".\venv\Scripts\Activate.ps1"

# Vérifier si les dépendances sont installées
$packageCheck = pip show python-dotenv 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Installation des dépendances..." -ForegroundColor Cyan
    pip install -r requirements.txt
}

# Vérifier si le fichier .env existe
if (!(Test-Path ".env")) {
    Write-Host "ERREUR: Le fichier .env n'existe pas!" -ForegroundColor Red
    Write-Host "Veuillez créer un fichier .env à partir de .env.example" -ForegroundColor Yellow
    Write-Host "Exemple: copy .env.example .env"
    Read-Host "Appuyez sur Entrée pour quitter"
    exit 1
}

# Vérifier FFmpeg
$ffmpegCheck = Get-Command ffmpeg -ErrorAction SilentlyContinue
if ($null -eq $ffmpegCheck) {
    Write-Host "ERREUR: FFmpeg n'est pas installé ou non accessible dans PATH" -ForegroundColor Red
    Write-Host "Veuillez installer FFmpeg: https://ffmpeg.org/download.html" -ForegroundColor Yellow
    Read-Host "Appuyez sur Entrée pour quitter"
    exit 1
}

# Vérifier NVIDIA CUDA
$cudaCheck = nvidia-smi 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "ATTENTION: NVIDIA CUDA n'est pas détecté" -ForegroundColor Yellow
    Write-Host "Le transcodage AV1 ne sera pas accéléré par GPU" -ForegroundColor Yellow
    Write-Host "Veuillez installer NVIDIA CUDA: https://developer.nvidia.com/cuda-downloads" -ForegroundColor Yellow
}

Write-Host "Lancement du script..." -ForegroundColor Cyan
python .\main.py

Read-Host "Appuyez sur Entrée pour quitter"
