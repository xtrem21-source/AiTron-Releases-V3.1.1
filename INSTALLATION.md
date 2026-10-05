# AiTron — INSTALLATION / INSTALLATION GUIDE

> **Langue / Language** — this file is the **switcher**. Choose your language:
> **Français** → [`INSTALLATION.fr.md`](INSTALLATION.fr.md) · **English** → [`INSTALLATION.en.md`](INSTALLATION.en.md)
> The interface itself follows the active language: `AiTron\Run-LocalAI.bat lang fr` / `lang en`.
>
> **Version v3.1.3** · **AiTron V3** — fork indépendant de LocalAI (licence MIT), enrichi d'une couche
> d'orchestration souveraine pour Windows. **Il n'est aucunement affilié au projet LocalAI officiel.**
> Le moteur conserve son nom d'origine (`local-ai.exe`) : seul le produit s'appelle AiTron V3.

---

## FR — Guide essentiel (autonome)

### 1. Prérequis
**Windows 10/11 64 bits** — **sans Docker, sans WSL**. **Python 3.10+** (pour lancer l'installeur ;
un runtime Python est embarqué dans le produit). **~12 Go** d'espace disque. GPU optionnel
(NVIDIA/Vulkan ; NPU Intel/Qualcomm via DirectML/OpenVINO). 8 Go de RAM minimum, 16+ recommandé.

### 2. Installation
```
1. Ouvrez un terminal à la racine de la sandbox (dossier contenant install_AiTron_v3.py).
2. python install_AiTron_v3.py          (--skip-model pour ignorer les modèles du catalogue)
3. Attendez la bascule transactionnelle.
4. Vérifiez :  AiTron\Run-LocalAI.bat status   puis   AiTron\Run-LocalAI.bat help
```
**Garanties** : sauvegarde ante-exécution du script maître dans `Installeur\` (`.py.txt` horodaté),
**validation AST triple** de tout fichier généré, **rollback** si la bascule échoue, et **refus
d'installation si des services tournent** (aucun fichier verrouillé ne peut détruire le produit).

### 3. Utilisation quotidienne
```
AiTron\Run-LocalAI.bat start | stop | restart | status | help
AiTron\Run-LocalAI.bat profile | set-profile <p> | benchmark [cpu] | vram-status
AiTron\Run-LocalAI.bat index <dossier> | rag-query <texte> | graph-index <d> | graph-show
AiTron\Run-LocalAI.bat mcp-list | mcp-call <s> <o> | quantize <m> <t> | privacy-test
AiTron\Run-LocalAI.bat hardware-status | vault-status | vault-seal | vault-unseal | vault-test
AiTron\Run-LocalAI.bat learn-profile | profile-status | reset-profile [soft|normal|hard]
AiTron\Run-LocalAI.bat peer-status | peer-scan | peer-test | lang [fr|en|list]
```
Points d'entrée : **http://127.0.0.1:4000** (gateway LiteLLM, authentifié — `Bearer sk-local`) et
**http://127.0.0.1:8080/v1** (API AiTron directe).

### 4. Clés cloud (BYOK) et confidentialité
`AiTron\Run-LocalAI.bat key-set openrouter <clé>` → écrit dans `config\keys.env` (jamais versionné).
Un **filtre PII hybride à 3 niveaux** masque les données personnelles avant tout appel cloud :
protection **au meilleur effort**, pas une garantie légale. L'inférence locale ne quitte jamais la machine.

### 5. GPU / NPU / CPU
**NVIDIA → Vulkan** (validé, sans CUDA ni DirectML) · **NPU Intel/Qualcomm → DirectML/OpenVINO** ·
⚠️ **NPU AMD XDNA2 via DirectML : EXPÉRIMENTAL ET NON FONCTIONNEL** (l'amont limite le NPU à Intel et
Qualcomm) → repli **CPU NumPy maîtrisé** · **CPU seul : pleinement fonctionnel**. Le moteur choisit
automatiquement et **retombe toujours** sur un chemin qui marche.

### 6. Fallbacks de téléchargement — GitHub Releases (v3.1.2)
L'installeur est **portable** : lance-le depuis n'importe quel dossier (clé USB, `C:\AiTron\`,
`D:\Projets\AiTron\`). La sandbox est le **dossier du script** ; l'option **`--root <chemin>`**
impose un autre répertoire cible. Si `local-ai.exe` / `cloud-proxy.exe` sont absents de `build\out\`,
ils sont repris du **staging archivé** (`dev\old\test_dynamique\AiTron\`), sinon **téléchargés** :
- `local-ai.exe`    : `https://github.com/xtrem21-source/AiTron-Releases-V3.1.1/releases/download/v3.1.2/local-ai.exe`  (SHA-256 `0F55C483…`)
- `cloud-proxy.exe` : `https://github.com/xtrem21-source/AiTron-Releases-V3.1.1/releases/download/v3.1.2/cloud-proxy.exe`  (SHA-256 `BFCB2804…`)
> **URLs GitHub Releases** (pérennes, binaires directs). Le **SHA-256** des binaires est **vérifié** et le
> **garde-fou PE `MZ`** s'applique à tout `.exe` téléchargé, avec ou sans somme attendue.

---

## EN — Essential guide (self-contained)

### 1. Prerequisites
**Windows 10/11 64-bit** — **no Docker, no WSL**. **Python 3.10+** (to run the installer; a Python
runtime is embedded in the product). **~12 GB** disk. GPU optional (NVIDIA/Vulkan; Intel/Qualcomm NPU
via DirectML/OpenVINO). 8 GB RAM minimum, 16+ recommended.

### 2. Installation
```
1. Open a terminal at the sandbox root (folder holding install_AiTron_v3.py).
2. python install_AiTron_v3.py          (--skip-model to skip catalogue models)
3. Wait for the transactional swap.
4. Verify:  AiTron\Run-LocalAI.bat status   then   AiTron\Run-LocalAI.bat help
```
**Guarantees**: pre-execution archive of the master script into `Installeur\` (timestamped `.py.txt`),
**triple AST validation** of every generated file, **rollback** if the swap fails, and **refusal to
install while services are running** (no locked file can destroy the product).

### 3. Daily use
```
AiTron\Run-LocalAI.bat start | stop | restart | status | help
AiTron\Run-LocalAI.bat profile | set-profile <p> | benchmark [cpu] | vram-status
AiTron\Run-LocalAI.bat index <folder> | rag-query <text> | graph-index <d> | graph-show
AiTron\Run-LocalAI.bat mcp-list | mcp-call <s> <o> | quantize <m> <t> | privacy-test
AiTron\Run-LocalAI.bat hardware-status | vault-status | vault-seal | vault-unseal | vault-test
AiTron\Run-LocalAI.bat learn-profile | profile-status | reset-profile [soft|normal|hard]
AiTron\Run-LocalAI.bat peer-status | peer-scan | peer-test | lang [fr|en|list]
```
Endpoints: **http://127.0.0.1:4000** (LiteLLM gateway, authenticated — `Bearer sk-local`) and
**http://127.0.0.1:8080/v1** (direct AiTron API).

### 4. Cloud keys (BYOK) and privacy
`AiTron\Run-LocalAI.bat key-set openrouter <key>` → writes `config\keys.env` (never versioned).
A **3-level hybrid PII filter** masks personal data before any cloud call: a **best-effort**
protection, not a legal guarantee. Local inference never leaves the machine.

### 5. GPU / NPU / CPU
**NVIDIA → Vulkan** (validated, no CUDA, no DirectML) · **Intel/Qualcomm NPU → DirectML/OpenVINO** ·
⚠️ **AMD XDNA2 NPU via DirectML: EXPERIMENTAL AND NON-FUNCTIONAL** (upstream limits NPU to Intel and
Qualcomm) → **mastered NumPy CPU fallback** · **CPU only: fully functional**. The engine selects
automatically and **always falls back** to a working path.

### 6. Download fallbacks — GitHub Releases (v3.1.2)
The installer is **portable**: run it from any folder (USB stick, `C:\AiTron\`, `D:\Projects\AiTron\`).
The sandbox is the **script's folder**; **`--root <path>`** overrides the target. If `local-ai.exe` /
`cloud-proxy.exe` are missing from `build\out\`, they are taken from the **archived staging**
(`dev\old\test_dynamique\AiTron\`), otherwise **downloaded** from:
- `local-ai.exe`    : `https://github.com/xtrem21-source/AiTron-Releases-V3.1.1/releases/download/v3.1.2/local-ai.exe`  (SHA-256 `0F55C483…`)
- `cloud-proxy.exe` : `https://github.com/xtrem21-source/AiTron-Releases-V3.1.1/releases/download/v3.1.2/cloud-proxy.exe`  (SHA-256 `BFCB2804…`)
> **GitHub Releases URLs** (permanent, direct binaries). The binary **SHA-256** is **verified** and the
> **PE `MZ` safeguard** applies to every downloaded `.exe`, with or without an expected checksum.

---

## Documentation detail / Détail
| Français | English |
|---|---|
| [`INSTALLATION.fr.md`](INSTALLATION.fr.md) — guide complet, 51 sections | [`INSTALLATION.en.md`](INSTALLATION.en.md) — full guide |
| `dev\CHANGELOG.md` — historique des versions | `dev\CHANGELOG.md` — version history |
| `dev\DECISIONS.md` — journal des décisions techniques | `dev\DECISIONS.md` — technical decisions |
| `ANOMALIES_NON_RÉSOLUES.log` — anomalies ouvertes | `ANOMALIES_NON_RÉSOLUES.log` — open anomalies |
