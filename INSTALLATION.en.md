# AiTron V3 — Installation and User Guide (English)

> Version **v3.0.0**. Reference document: `INSTALLATION.fr.md` (French). This English edition covers
> the same product surface; where wording differs, the French reference prevails.

## 0. Transparency notice
**AiTron V3 is an independent fork of LocalAI (MIT licence), enriched with a sovereign orchestration
layer for Windows. It is in no way affiliated with the official LocalAI project.**
The inference engine keeps its upstream name (`local-ai.exe`) and remains the unchanged technological
core; only the contextual inference product is named **AiTron V3**.

## 1. Prerequisites
| Item | Requirement |
|---|---|
| OS | **Windows 10 or 11 (64-bit)** — **no Docker, no WSL** |
| Python | **3.10+** (only to run the installer; an embedded runtime ships with the product) |
| Disk | **~12 GB** (engines, embedded runtimes, backend models) — more for large models |
| GPU | Optional. **NVIDIA (Vulkan)**, Intel/Qualcomm NPU (DirectML/OpenVINO) when present |
| RAM | 8 GB minimum, **16 GB+ recommended** |

## 2. Installation, step by step
```
1. Open a terminal in the sandbox root (folder holding install_AiTron_v3.py).
2. Run:            python install_AiTron_v3.py
   Options: --skip-model           skip the optional catalogue downloads
            --prev <path>          explicit heritage source (e.g. a backup)
3. Wait. The installer builds a staging tree, then performs a TRANSACTIONAL swap.
   Nothing is deleted before the new tree is proven complete.
4. Expected final lines:
      "manifest.json written: N components"
      "Product switched transactionally to ...\AiTron"
      "Deployment complete."
5. Verify:
      AiTron\Run-LocalAI.bat status
      AiTron\Run-LocalAI.bat help
```
**Safety guarantees** — before any change: the master script is archived to `Installeur\`
(timestamped `.py.txt`); **triple AST validation** runs on every generated file; a **rollback** restores
the previous tree if the swap fails; and the installer **refuses to run while services are active**
(a locked file can therefore never destroy the product).
**Heritage rule** — user data survives every reinstall: `config\keys.env`, `config\cloud-keys.env`,
`config\mcp-settings.json`, `config\failover.json`, `config\profile.json`, `config\lang.json`,
`i18n\fr.json`, `i18n\en.json`, `logs\history.jsonl`, `runtime\rag`, `runtime\storage`, `runtime\onnx`
and every downloaded model. If `AiTron\` does not exist yet but the legacy `LocalAI\` does, the
installer **inherits from the legacy folder automatically**.

## 3. Daily use
```
AiTron\Run-LocalAI.bat start      :: core + engines + gateway + watchdog (+ RPC discovery)
AiTron\Run-LocalAI.bat stop       :: stops everything (zero zombie)
AiTron\Run-LocalAI.bat status     :: PID / ports / availability
AiTron\Run-LocalAI.bat help       :: full command list (in the active language)
```
Default endpoints: **http://127.0.0.1:4000** (LiteLLM gateway, authenticated) and
**http://127.0.0.1:8080/v1** (direct AiTron API).

### 3.1 Main commands
| Command | Purpose |

## 4. Cloud API keys (anonymised BYOK)
Keys live in **`AiTron\config\keys.env`** (external providers) and `config\cloud-keys.env`; they are
**never hard-coded** and **never versioned**.
```
AiTron\Run-LocalAI.bat key-set openrouter <your_key>
AiTron\Run-LocalAI.bat key-set openai     <your_key>
```
Supported: OpenRouter, OpenAI, Anthropic, DeepSeek.
**PII filter (best-effort)** — before any cloud call, a **3-level hybrid filter** masks personal data
(structured patterns + heuristics + optional NER). This protection is **best-effort by design, not a
legal guarantee**: never send data you are not allowed to disclose. Local inference never leaves the
machine.

## 5. Heterogeneous GPU / NPU / CPU architecture
| Layer | Status |
|---|---|
| **NVIDIA GPU** | **Vulkan** — tested and validated (no CUDA, no DirectML needed) |
| **Intel / Qualcomm NPU** | Addressable via **DirectML** or **OpenVINO**, when present |
| **AMD NPU (XDNA2)** | EXPERIMENTAL AND NON-FUNCTIONAL. Upstream DirectML limits NPU support to Intel and Qualcomm. AMD therefore relies on the **mastered CPU (native NumPy) fallback**. |
| **CPU only** | Fully functional: RAG, GraphRAG, embeddings, quantized inference |

The engine **selects the best available layer automatically** and **always falls back** to a working
path (RPC federation -> CPU-pure `-ngl 0` -> NumPy). No layer is mandatory.

## 6. Adaptive learning profile
The machine **tunes itself** from its own real measurements; the factory reset is guaranteed.
```
AiTron\Run-LocalAI.bat profile-observe   :: record one session observation
AiTron\Run-LocalAI.bat learn-profile     :: recompute thresholds -> config\profile.json
AiTron\Run-LocalAI.bat profile-status    :: learned vs factory, active thresholds
AiTron\Run-LocalAI.bat reset-profile soft:: INSTANT factory reset (soft|normal|hard)
```
The VRAM alert threshold is anchored on the **lowest free-VRAM actually observed** (+5 pt margin);
all thresholds are **bounded**; `-ngl` is reduced only when real critical evictions were logged. The
watchdog **re-reads the profile every 5 s**, so changes apply **live, with no restart**.

## 7. Federated inference (RPC) and network discovery
- Discovery is **non-invasive UDP broadcast in pure Python** (no `zeroconf`): it only collects node
  addresses — **no inference data is ever transmitted** by it.
- Computation transport is **delegated 100 % to the native llama.cpp RPC core** through the exact
  `--rpc <IP>:<Port>` argument. On a remote machine, run the engine's own server:
  `ggml-rpc-server.exe -H 0.0.0.0 -p 50052` (real upstream binary name; default port **50052**).
- **Safety**: an **unreachable** node is never used — on an isolated machine everything stays
  **100 % local** and inference is never broken.

## 8. Encrypted vault (AES-256)
```
AiTron\Run-LocalAI.bat vault-seal     :: encrypt runtime\rag and runtime\storage (password asked, masked)
AiTron\Run-LocalAI.bat vault-unseal   :: restore them for the session
AiTron\Run-LocalAI.bat vault-status   :: sealed / plaintext inventory
AiTron\Run-LocalAI.bat vault-test     :: self-test (seal, open, integrity, wrong-password refusal)
```
**Transparency**: protection applies **at rest only**; RAM erasure is **not guaranteed**; the key is
**never written to disk** (PBKDF2-HMAC-SHA256, 390 000 iterations, random salt) and a forgotten
password means **permanently lost data** — there is no backdoor.

## 9. Language (i18n, FR/EN)
```
AiTron\Run-LocalAI.bat lang          :: show the active language
AiTron\Run-LocalAI.bat lang en       :: switch to English IMMEDIATELY (banner included)
AiTron\Run-LocalAI.bat lang list     :: list available codes
```
**Three-layer design** — (1) **embedded dictionary** inside `i18n.py` (ultimate source of truth);
(2) **external JSON** `i18n\fr.json` and `i18n\en.json` (generated at install, user-customisable);
(3) **revision constant `I18N_REV`** — when it changes, only documentation keys (`help_*`, `tip_*`) are
refreshed from the embedded layer, so your own message edits survive updates.
Priority: `AITRON_LANG` -> `config\lang.json` -> default `fr`. A missing or corrupt JSON file falls back
**silently** to the embedded layer; the product never crashes over a language file.

## 10. Troubleshooting
| Symptom | Action |
|---|---|
| Installer refuses to run | Services are active: run `Run-LocalAI.bat stop` first |
| Gateway returns **401** | Expected: the gateway is authenticated. Use `Authorization: Bearer sk-local` |
| Whisper `/v1/models` returns **404** | Normal: whisper.cpp does not expose that route. Use `/` or `/health` |
| No GPU acceleration | Run `Run-LocalAI.bat hardware-status`; the CPU fallback always works |
| No federated peer | `peer-status` -> "none" is the normal state on an isolated machine |
| Language looks unchanged | `lang list`, then `lang fr` / `lang en`; check `config\lang.json` |
| Something looks broken | Read `dev\crash.log` and `dev\patch_integrity.log`; `ANOMALIES_NON_RÉSOLUES.log` lists known upstream limitations |

|---|---|
| `start` / `stop` / `restart` | Lifecycle of the whole stack |
| `profile` / `set-profile <p>` | Show / change the profile: `soft\|normal\|hard\|auto\|custom` |
| `benchmark [cpu]` | Measure tokens/s (GPU by default) |
| `vram-status` | Total/used/free VRAM, thresholds, watchdog state |
| `index <folder>` | Index a folder — **multi-format RAG**: txt, md, json, py, pdf, docx, xlsx, images |
| `rag-query <text>` | Cosine search inside the local RAG index |
| `graph-index <d>` / `graph-show` | Build / inspect the local **GraphRAG** graph |
| `mcp-list` / `mcp-call <s> <o>` | List / call MCP tools (official SDK, spec 2024-11-05) |
| `quantize <m> <t>` | Local quantization (`llama-quantize`): F16 -> Q4_K_M / Q8_0 / ... |
| `privacy-test` / `privacy-levels` | PII filter self-test / the 3 masking levels |
| `hardware-status` | Workload split (main GPU vs semantic tasks) |
| `vault-status` / `vault-seal` / `vault-unseal` / `vault-test` | AES-256 vault of the semantic zone |
| `learn-profile` / `profile-status` / `reset-profile` | Adaptive profile (see section 6) |
| `peer-status` / `peer-scan` / `peer-test` / `peer-rpc-arg` | Federated RPC discovery (see section 7) |
| `lang [fr\|en\|list]` | Show / switch the interface language **live** |
| `i18n-status` / `i18n-test` | i18n state / self-test |
