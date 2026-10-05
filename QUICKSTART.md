# Quickstart — AiTron V3 en 5 minutes

## 1. Prerequis
- Windows 10/11 64 bits
- Python 3.10+ (pour lancer l'installeur)
- ~12 Go d'espace disque
- 8 Go de RAM minimum
- Pas besoin de Docker, pas besoin de WSL

## 2. Installation
    cd G:\V1\LocalAI-Projet
    python install_AiTron_v3.py

## 3. Demarrage
    cd AiTron
    Run-LocalAI.bat start
    Run-LocalAI.bat status

## 4. Premier test
Navigateur : http://127.0.0.1:8080/app
API : http://127.0.0.1:8080/v1/models

## 5. Arret
    Run-LocalAI.bat stop

## Commandes de base
| Commande | Action |
|----------|--------|
| Run-LocalAI.bat start | Demarre |
| Run-LocalAI.bat stop | Arrete |
| Run-LocalAI.bat status | Etat |
| Run-LocalAI.bat help | Aide |
| Run-LocalAI.bat profile | Profil materiel |
| Run-LocalAI.bat benchmark | Tokens/s |
| Run-LocalAI.bat lang fr | Francais |
| Run-LocalAI.bat lang en | Anglais |

## Apres
- INSTALLATION.md : installation complete
- ARCHITECTURE.md : architecture
- SECURITY.md : securite
- INSTALLATION.fr.md / .en.md : documentation utilisateur
