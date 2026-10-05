#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Extraction read-only de la verite technique (CLI, env, ports)."""
import re, io
P = r"G:\V1\LocalAI-Projet\install_AiTron_v3.py"
d = io.open(P, encoding="utf-8", errors="replace").read()
print("LIGNES:", len(d.splitlines()))
print("VERSION:", [l.strip() for l in d.splitlines() if "__version__ =" in l][:2])
# 1. bloc COMMANDS / dispatch du wrapper
for pat in [r"COMMANDS\s*=\s*\{", r"def\s+\w*dispatch\w*\(", r"Run-LocalAI", r"run_bat|gen_run|RUN_BAT"]:
    m = [l.strip()[:140] for l in d.splitlines() if re.search(pat, l)]
    print("PAT", pat, "->", len(m))
    for l in m[:15]:
        print("   ", l)
# 2. noms de commandes cites dans les aides (Run-LocalAI.bat xxx)
cmds = sorted(set(re.findall(r"Run-LocalAI\.bat\s+([a-z][a-z0-9\-]*)", d)))
print("CMDS_VIA_RUNBAT(%d):" % len(cmds))
print(cmds)
# 3. variables d'environnement
envs = sorted(set(re.findall(r"(?:os\.environ\.get\(\s*|os\.getenv\(\s*|set\s+)([A-Z][A-Z0-9_]{3,})", d)))
print("ENVS(%d):" % len(envs))
print(envs)
# 4. ports
ports = sorted(set(re.findall(r"\b(4\d{3}|80\d{2}|809\d|50052|47653)\b", d)))
print("PORTS:", ports)
# 5. AITRON_DEPLOY_CODE / LOCALAI_DEPLOY_CODE
print("AITRON_DEPLOY_CODE:", d.count("AITRON_DEPLOY_CODE"))
print("LOCALAI_DEPLOY_CODE:", d.count("LOCALAI_DEPLOY_CODE"))
print("install_localai_win:", d.count("install_localai_win"))
print("install_AiTron_v3:", d.count("install_AiTron_v3"))
print("AITRON_LANG:", d.count("AITRON_LANG"), "LOCALAI_LANG:", d.count("LOCALAI_LANG"))
print("AITRON_SPEC:", d.count("AITRON_SPEC"))
print("I18N_REV:", d.count("I18N_REV"))
