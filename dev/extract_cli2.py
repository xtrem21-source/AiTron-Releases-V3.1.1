#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Passage 2 : aide embarquee, dispatch bat, variables d'env (toutes formes)."""
import re, io
P = r"G:\V1\LocalAI-Projet\install_AiTron_v3.py"
d = io.open(P, encoding="utf-8", errors="replace").read()
# A. toutes les cles msg_help_* (aide FR + EN embarquee)
keys = sorted(set(re.findall(r'"(msg_help_[a-z0-9_]+)"', d)))
print("HELP_KEYS(%d):" % len(keys)); print(keys)
# B. commandes citees dans les textes d'aide (if "%1"== / goto / :cmd)
batcmds = sorted(set(re.findall(r'if\s+["\']?%1["\']?\s*==\s*["\']?([a-z][a-z0-9\-]*)', d, re.I)))
gotocmds = sorted(set(re.findall(r'goto\s+:?([a-z][a-z0-9\-_]*)', d, re.I)))
print("BAT_IF(%d):" % len(batcmds)); print(batcmds)
print("GOTO(%d):" % len(gotocmds)); print([g for g in gotocmds if len(g) < 25][:80])
# C. variables d'env : toutes formes (getenv, environ[], SET , AITRON_/LOCALAI_)
envs = sorted(set(re.findall(r'getenv\(\s*"([A-Z][A-Z0-9_]+)"', d)))
envs += sorted(set(re.findall(r'environ\[\s*"([A-Z][A-Z0-9_]+)"', d)))
envs += sorted(set(re.findall(r'\bSET\s+([A-Z][A-Z0-9_]+)=', d)))
envs += sorted(set(re.findall(r'\b((?:AITRON|LOCALAI)_[A-Z0-9_]+)\b', d)))
envs = sorted(set(envs))
print("ENVS(%d):" % len(envs)); print(envs)
# D. lignes d'aide completes (pour la reference CLI fidele)
for m in re.finditer(r'"msg_help_cmd_[a-z0-9_]+":\s*"([^"]+)"', d):
    print("HELP:", m.group(1)[:150])
