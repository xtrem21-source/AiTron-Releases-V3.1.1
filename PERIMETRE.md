# PERIMETRE.md — Contrat de Confinement Auto-Declare

> Produit par l'agent AVANT toute action significative. Si l'agent viole ce contrat, il est en faute.

## 1. Perimetre d'action unique

```
G:\V1\LocalAI-Projet\
```

Toute lecture et toute ecriture restent strictement dans ce sous-arbre de G:\.

## 2. Zones et droits

| Zone | Chemin | Droit |
|------|--------|-------|
| Racine (contrat) | G:\V1\LocalAI-Projet\ | Ecriture libre : script maitre, charte, docs |
| Laboratoire | G:\V1\LocalAI-Projet\dev\ | Ecriture libre, a plat (sauf old\) |
| Quarantaine | G:\V1\LocalAI-Projet\dev\old\ | Mise a l'ecart, rien n'est supprime |
| Boite noire | G:\V1\LocalAI-Projet\Installeur\ | Ecriture controlee (archive_installer() uniquement) |
| Logs | G:\V1\LocalAI-Projet\log\ | Append-only |
| Build (chantier) | G:\V1\LocalAI-Projet\build\ | Espace de compilation (outils + sources + telechargements). Ajoute et documente dans DECISIONS.md ; hors dev\, donc non contraire a 2.4. |
| Produit deploye | G:\V1\LocalAI-Projet\AiTron\ | Ecriture via l'installeur uniquement ; effacable par l'utilisateur |
| Livrable (script maitre) | G:\V1\LocalAI-Projet\install_AiTron_v3.py | Ecriture via patch chirurgical + validation AST |
| Documentation racine | G:\V1\LocalAI-Projet\INSTALLATION*.md, ANOMALIES_NON_RÉSOLUES.log | Ecriture libre (livrables de cloture) |

## 3. Dossiers sensibles hors sandbox — LECTURE SEULE INTERDITE

- C:\Windows\System32 (sauf usage d'executables natifs : taskkill, curl, tar, powershell, cmd)
- C:\Program Files, C:\Program Files (x86)
- C:\Users\* (aucune lecture ni ecriture)
- Tout chemin hors de G:\V1\LocalAI-Projet\

L'agent n'ecrit JAMAIS hors de la sandbox et ne lit aucun fichier utilisateur hors sandbox. La seule
interaction externe autorisee est le telechargement reseau (HTTPS) vers la sandbox.

## 4. Interdictions absolues

- Sortir de G:\V1\LocalAI-Projet\ (lecture ou ecriture de fichiers)
- Ecrire/modifier/supprimer un fichier hors sandbox
- Creer des sous-dossiers dans dev\ (sauf old\)
- Supprimer definitivement un fichier sans le deplacer d'abord dans old\
- Toucher aux dossiers sensibles listes en section 3
- Packaging monolithique (PyInstaller, fusion en un unique binaire)
- Docker, WSL sauf dernier recours documente

## 5. URLs autorisees au telechargement (HTTPS uniquement)

### Sources officielles LocalAI
- https://github.com/mudler/LocalAI
- https://github.com/mudler/LocalAI/releases
- https://localai.io/

### Outils et compilateurs
- https://go.dev/dl/
- https://git-scm.com/download/win
- https://github.com/ggml-org/llama.cpp/releases
- https://github.com/ggml-org/whisper.cpp/releases
- Outil CGO MinGW-w64 : https://github.com/niXman/mingw-builds-binaries/releases
  (justifie dans DECISIONS.md : CGO requis par mattn/go-sqlite3, aucune source GCC officielle Windows)

### Modeles de test
- https://huggingface.co/
- https://huggingface.co/bartowski/Llama-3.2-1B-Instruct-GGUF

### Environnement Python
- https://www.python.org/downloads/windows/
- https://pypi.org/

### API de metadonnees
- https://api.github.com/ (metadonnees de releases, lecture seule)
- https://raw.githubusercontent.com/ (lecture de fichiers de source)

### Phase 2 (v1.2.0) — sources des backends multi-modaux et de l'environnement embarque
- https://github.com/ggml-org/whisper.cpp/releases (backend speech-to-text ; asset
  `whisper-bin-Win32.zip`, tag v1.9.2)
- https://github.com/leejet/stable-diffusion.cpp/releases (backend image ;
  asset `sd-master-3f8527a-bin-win-cpu-x64.zip`)
- https://github.com/thewh1teagle/kokoro-onnx/releases (TTS ; `model-files-v1.1`)
- https://huggingface.co/ggerganov/whisper.cpp (modele `ggml-base.bin`)
- https://huggingface.co/stabilityai/sd-turbo (modele image, non telecharge par defaut)
- https://www.python.org/ftp/python/3.11.9/ (Python 3.11.9 embed amd64)
- https://bootstrap.pypa.io/get-pip.py (bootstrap pip)
- https://pypi.org/ (paquets : litellm[proxy]==1.103.2, kokoro-onnx, soundfile, onnxruntime)
- https://nodejs.org/dist/ et https://github.com/protocolbuffers/protobuf/releases
  (outils de reconstruction du coeur — cf. DECISIONS.md D-007/D-008)

Toute autre source doit etre justifiee dans dev/DECISIONS.md avec URL exacte, raison et hash SHA-256.

## 5bis. Nouvelles zones internes du produit (Phase 2)

| Zone (dans le produit) | Contenu | Droit |
|------------------------|---------|-------|
| `LocalAI\runtime\python\` | Python 3.11.9 embarque (LiteLLM + TTS) | Ecriture via l'installeur |
| `LocalAI\scripts\` | Helpers PowerShell (up/status/model_manager/…) | Ecriture via l'installeur |
| `LocalAI\data\` | Etat d'execution (pids.txt, runtime.env) | Ecriture runtime uniquement |
| `LocalAI\config\cloud-keys.env` | Cles API externes (BYOK) | **jamais versionne**, conserve entre installs |

Aucune de ces zones ne sort de la sandbox `G:\V1\LocalAI-Projet\`.

### Phase 3 (v1.3.0) — sources GPU et zones ajoutees
- https://github.com/ggml-org/llama.cpp/releases — variantes GPU du moteur :
  `llama-b11375-bin-win-vulkan-x64.zip`, `llama-b11375-bin-win-cuda-12.4-x64.zip`,
  `llama-b11375-bin-win-rocm-10.0-x64.zip` (hip), `llama-b11375-bin-win-cpu-x64.zip`,
  et le runtime `cudart-llama-bin-win-cuda-12.4-x64.zip`
- https://github.com/leejet/stable-diffusion.cpp/releases — variante image GPU
  `sd-master-3f8527a-bin-win-cuda12-x64.zip`
- https://pypi.org/ — `onnxruntime` (provider CPU de reference ; DirectML testé puis écarté)

| Zone (produit) | Contenu | Droit |
|---|---|---|
| `LocalAI\backends\llama-cpp\variants\{cpu,vulkan,cuda}\` | variantes du moteur | remplaçables individuellement |
| `LocalAI\config\hardware-profile.json` | profil matériel persistant | regénéré par `optimize` |
| `LocalAI\config\bench-history.jsonl` | historique des benchmarks | append-only |
| `LocalAI\scripts\{hw_profile,engine_select,bench}.ps1` | outils GPU/matériel | via l'installeur |

### Phase 4 (v1.4.0) — sources RAG et zones ajoutees
- https://pypi.org/ — packages isolés du pipeline RAG : `numpy>=1.24.0`, `pypdf>=4.0.0`,
  `python-docx`, `openpyxl` (installés via `pip --target` dans `runtime\packages`).
- **Aucune source supplémentaire** pour les embeddings : le moteur llama.cpp déjà présent expose
  `/v1/embeddings` (flag `--embeddings --pooling mean`). `faiss` est **proscrit** (mandat §1.1).

| Zone (produit) | Contenu | Droit |
|---|---|---|
| `LocalAI\runtime\rag\` | index vectoriel à plat (`.npy`, `.jsonl`, manifest) | écrit par `index`, lu par `rag-query` |
| `LocalAI\runtime\packages\` | packages RAG isolés (`pip --target`) | via l'installeur |
| `LocalAI\config\keys.env` | clés API externes (BYOK) | **jamais versionné**, préservé entre installs |
| `LocalAI\scripts\rag_ingest.py` | pipeline RAG (extraction/chunking/recherche) | via l'installeur |
| `LocalAI\logs\routing.jsonl` | journal des décisions du Token Saver | append-only |
| Processus | serveur d'embeddings à la demande (port 8094) | tracé dans `data\pids.txt` |

Aucune de ces zones ne sort de la sandbox `G:\V1\LocalAI-Projet\`.

## 6. Outils natifs Windows utilises

taskkill, powershell, curl.exe, tar.exe, cmd.exe — natifs, non modifies.

## 8. Services et ports exposes (v1.6.0)

Tous les services ecoutent en **127.0.0.1** uniquement (aucune exposition reseau) :

| Port | Service | Role |
|---|---|---|
| 8080 | coeur LocalAI | API OpenAI-compatible |
| 8081 | **failover proxy** | bufferisation + bascule locale/cloud |
| 8090 | llama-server | moteur texte (GPU) |
| 8091 | whisper-server | transcription audio |
| 8092 | sd-server | generation d'image |
| 8093 | tts-server | synthese vocale |
| 8094 | embed-server | embeddings RAG (a la demande) |
| 8095 | **moteur vision** | VLM `--mmproj` (CPU) |
| 4000 | gateway LiteLLM | routage local/externe (BYOK) |

## 9. Confidentialite et acceleration (v1.7.0 / v1.8.0)

- **Filtre PII** : le masquage s'effectue **localement**, dans le processus du Token Saver
  (`config\complexity_router.py`) ; seuls des jetons `[PII-TYPE-n]` sont transmis a une API distante
  lors d'un debordement cloud. Le mapping de restitution ne quitte **jamais** la machine.
  Protection **BEST-EFFORT** (non garantie a 100 %), desactivable par `--no-pii-filter`.
  Audit local : `dev\crash.log`, categorie `PRIVACY_FILTER` (apercus tronques, jamais le secret).
- **Quantization** : entierement locale (`llama-quantize.exe`), historique dans
  `data\quantize-history.jsonl`.
- **Acceleration NPU** : `onnxruntime-directml` installe dans le Python embarque
  (`runtime\python\Lib\site-packages`) ; modele sonde `runtime\onnx\mnist-8.onnx` (25 843 octets,
  SHA-256 `2f06e72d...c9bf`). Repli CPU automatique, avertissement local `dev\crash.log`
  (categorie `GPU_DETECT`).
- Le nouvel outil MCP `localai_semantic_probe` **n'ouvre aucune connexion reseau** : la sonde
  s'execute en local sur le provider retenu.

---
*Confinement declare le 2026-10-03. Auto-controle : aucune commande de l'agent ne sort du perimetre.*
