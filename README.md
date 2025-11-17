# 🎥 Python Transcode AV1

Un outil de transcodage vidéo automatisé qui convertit des vidéos au format AV1 avec gestion audio et sous-titres avancée.

> **Auteur** : WolfDry  
> **Licence** : MIT

---

## 📋 Table des matières

- [Caractéristiques](#caractéristiques)
- [Prérequis](#prérequis)
- [Installation](#installation)
- [Configuration](#configuration)
- [Utilisation](#utilisation)
- [Architecture](#architecture)
- [Formats supportés](#formats-supportés)
- [Résolution et paramètres AV1](#résolution-et-paramètres-av1)
- [Dépannage](#dépannage)

---

## ✨ Caractéristiques

### 🎬 Conversion vidéo
- ✅ Transcodage au codec **AV1**
- ✅ Accélération matérielle **NVIDIA CUDA** (AV1 NVENC)
- ✅ Détection automatique HDR (Rec. 2020, ST 2084, etc.)
- ✅ Adaptation intelligente des paramètres selon la résolution

### 🔊 Gestion audio
- ✅ Transcodage en **AAC**
- ✅ Détection de la langue des pistes audio
- ✅ Conservation des métadonnées (titre, langue, handler_name)
- ✅ Support multi-canaux (mono, stéréo, 5.1, 7.1, etc.)
- ✅ Détection et suppression optionnelle des pistes spéciales (VFQ, audio descriptive)

### 📝 Gestion des sous-titres
- ✅ Support des formats SRT, ASS, SSA, MOV_TEXT
- ✅ Détection des sous-titres forcés
- ✅ Détection des sous-titres malentendants
- ✅ Conservation des métadonnées des sous-titres

### 🛡️ Robustesse
- ✅ Validation des répertoires avant traitement
- ✅ Gestion d'erreurs complète avec nettoyage automatique
- ✅ Logs détaillés avec timestamps et codes couleur
- ✅ Traitement par lot de fichiers avec compteur de succès

---

## 📦 Prérequis

### Système d'exploitation
- **Windows 10/11** (avec support PowerShell)
- Testé sur Windows 10+

### Logiciels requis
- **Python** 3.8+
- **FFmpeg** et **FFprobe** (disponibles dans PATH)
- **NVIDIA CUDA Toolkit** (pour accélération matérielle)
- Carte graphique NVIDIA compatible avec NVENC AV1

### Installation des dépendances système

#### 1. FFmpeg (via Chocolatey)
```powershell
choco install ffmpeg
```

Ou télécharger manuellement : https://ffmpeg.org/download.html

#### 2. NVIDIA CUDA Toolkit
- Télécharger : https://developer.nvidia.com/cuda-downloads
- Installer le toolkit complet
- Vérifier avec : `nvidia-smi`

---

## 🚀 Installation

### 1. Cloner le repository
```bash
git clone https://github.com/WolfDry/Python-Transcode-AV1.git
cd Python-Transcode-AV1
```

### 2. Créer un environnement virtuel
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 3. Installer les dépendances Python
```bash
pip install -r requirements.txt
```

### 4. Configurer les variables d'environnement
```bash
cp .env.example .env
```

Éditer le fichier `.env` avec vos chemins :
```env
OUTPUT_PATH=C:\Videos\Output
TEMP_PATH=C:\Videos\Temp
```

---

## ⚙️ Configuration

### Variables d'environnement (.env)

| Variable | Description | Exemple |
|----------|-------------|---------|
| `OUTPUT_PATH` | Dossier de destination des vidéos transcodes | `C:\Videos\Output` |
| `TEMP_PATH` | Dossier temporaire pour les fichiers intermédiaires | `C:\Videos\Temp` |

**Important** : Les dossiers doivent exister avant de lancer le script.

### Création des dossiers
```powershell
New-Item -ItemType Directory -Force -Path "C:\Videos\Output"
New-Item -ItemType Directory -Force -Path "C:\Videos\Temp"
```

---

## 📖 Utilisation

### Lancer le script
```powershell
python .\main.py
```

### Exemple d'exécution
```
Entrez le répertoire contenant les fichiers vidéo à traiter : C:\Videos\Input
3 fichier(s) vidéo trouvé(s) dans le répertoire C:\Videos\Input.

============================================================
Traitement du fichier : movie1.mkv
============================================================
[INFO] 14:23:45 | [Étape 1/3] Conversion en MP4...
[OK] 14:25:12 | ✅ Conversion en MP4 terminée.
[INFO] 14:25:13 | [Étape 2/3] Transcodage audio...
[OK] 14:26:45 | ✅ Transcodage audio terminé.
[INFO] 14:26:46 | [Étape 3/3] Transcodage vidéo AV1...
[OK] 14:45:30 | ✅ Transcodage vidéo AV1 terminé.
[OK] 14:45:31 | ✅ Fichier final sauvegardé : C:\Videos\Output\movie1.mp4

============================================================
Traitement terminé : 3/3 fichier(s) traité(s) avec succès.
============================================================
```

---

## 🏗️ Architecture

```
Python-Transcode-AV1/
├── main.py                          # Point d'entrée principal
├── models/
│   ├── convert_to_mp4.py           # Conversion MP4 et gestion sous-titres
│   ├── transcode_audio.py          # Transcodage audio AAC
│   └── transcode_av1.py            # Transcodage vidéo AV1
├── utils/
│   ├── __init__.py                 # Export des classes
│   ├── audio.py                    # Classes audio (AudioTrack, AudioStream)
│   └── video.py                    # Classes vidéo (VideoTrack, TranscodeData)
├── .env                            # Variables d'environnement (à créer)
├── .env.example                    # Exemple de configuration
└── README.md                       # Cette documentation
```

### Pipeline de traitement

```
Video Source
     ↓
[1] convert_to_mp4.py
    └─ Conversion en MP4 + Sous-titres
         ↓
[2] transcode_audio.py
    └─ Transcodage audio AAC
         ↓
[3] transcode_av1.py
    └─ Transcodage vidéo AV1 (CUDA)
         ↓
Output (MP4 AV1)
```

---

## 🎯 Formats supportés

### Entrée
- `.mp4` - MPEG-4
- `.mkv` - Matroska
- `.avi` - Audio Video Interleave
- `.mov` - QuickTime

### Sortie
- `.mp4` - MPEG-4 avec :
  - Vidéo : AV1 (NVIDIA NVENC)
  - Audio : AAC
  - Sous-titres : MOV_TEXT (convertis depuis SRT, ASS, SSA)

---

## 🎬 Résolution et paramètres AV1

Le script adapte automatiquement les paramètres AV1 selon la résolution détectée :

| Résolution | CQ (Qualité) | Tile Columns | Bitrate Cible |
|-----------|-------------|--------------|---------------|
| 2160p (4K) | 26-27 | 2 | 60-70% source |
| 1440p (QHD) | 29 | 1 | 50-65% source |
| 1080p (FHD) | 31 | 1 | 45-60% source |
| 720p (HD) | 33 | 1 | 40-55% source |

### Paramètres avancés
- **Codec vidéo** : AV1 NVENC (GPU-accéléré)
- **Preset** : p3 (performance 3 - qualité optimale)
- **RC Mode** : VBR (Variable Bitrate)
- **Lookahead** : 32 frames
- **Spatial-AQ** : Enabled
- **Temporal-AQ** : Enabled
- **GOP** : 2 × FPS
- **Color space** : Automatique (BT.709 ou BT.2020 pour HDR)

---

## 🐛 Dépannage

### ❌ "Les variables d'environnement OUTPUT_PATH et TEMP_PATH doivent être définies"
**Solution** : Créer/éditer le fichier `.env` à la racine du projet
```env
OUTPUT_PATH=C:\Videos\Output
TEMP_PATH=C:\Videos\Temp
```

### ❌ "Le répertoire de sortie n'existe pas"
**Solution** : Créer les répertoires manuellement
```powershell
New-Item -ItemType Directory -Force -Path "C:\Videos\Output"
New-Item -ItemType Directory -Force -Path "C:\Videos\Temp"
```

### ❌ "ffmpeg: not found" ou "ffprobe: not found"
**Solution** : Installer FFmpeg et l'ajouter au PATH
1. Télécharger FFmpeg : https://ffmpeg.org/download.html
2. Ajouter le dossier `bin` au PATH système
3. Vérifier : `ffmpeg -version`

### ❌ "NVIDIA CUDA not found"
**Solution** : 
1. Installer NVIDIA CUDA Toolkit
2. Installer les drivers NVIDIA récents
3. Vérifier : `nvidia-smi`

### ⚠️ Transcodage très lent
**Vérifications** :
- Vérifier que la GPU est bien utilisée : `nvidia-smi`
- Vérifier les ressources disponibles
- Vérifier que le disque temporaire a assez d'espace libre

## 📊 Estimation de temps

Pour une vidéo **FHD (1080p, 2h, 5 Mbps)** :
- Conversion MP4 : ~10 minutes
- Transcodage audio : ~5 minutes
- Transcodage vidéo AV1 : ~30-60 minutes (selon GPU)
- **Total** : ~45-75 minutes
- **Réduction taille** : ~60-70%

---

## 🔗 Ressources

- [FFmpeg Documentation](https://ffmpeg.org/documentation.html)
- [AV1 Codec](https://aomedia.org/av1/)
- [NVIDIA NVENC Documentation](https://developer.nvidia.com/nvidia-video-codec-sdk)
- [Python dotenv](https://github.com/theskumar/python-dotenv)

---

## 📝 Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.

---

## 🤝 Contribution

Les contributions sont bienvenues ! N'hésitez pas à :
- Signaler des bugs
- Proposer des améliorations
- Soumettre des pull requests

---

## 📧 Contact

**WolfDry** - [GitHub](https://github.com/WolfDry)

---

**Dernière mise à jour** : November 17, 2025
