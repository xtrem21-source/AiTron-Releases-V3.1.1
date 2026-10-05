#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
backup_installation_fr.py - Sauvegarde AVANT reecriture de INSTALLATION.fr.md
Ne supprime jamais rien. Copie horodatee + verification SHA-256.
"""
from __future__ import annotations
import argparse, hashlib, os, shutil, sys, time

SANDBOX  = r"G:\V1\LocalAI-Projet"
SOURCE   = os.path.join(SANDBOX, "INSTALLATION.fr.md")
OLD_DIR  = os.path.join(SANDBOX, "dev", "old")
LOG_DIR  = os.path.join(SANDBOX, "log")
LOG_FILE = os.path.join(LOG_DIR, "backup_installation_fr.log")


def log(msg):
    line = "[%s] %s" % (time.strftime("%Y-%m-%d %H:%M:%S"), msg)
    print(line)
    try:
        os.makedirs(LOG_DIR, exist_ok=True)
        with open(LOG_FILE, "a", encoding="utf-8") as fh:
            fh.write(line + "\n")
    except Exception:
        pass


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1048576), b""):
            h.update(block)
    return h.hexdigest()


def deja_aujourdhui():
    stamp = time.strftime("%Y%m%d")
    prefix = "INSTALLATION.fr_%s" % stamp
    out = []
    if os.path.isdir(OLD_DIR):
        for name in sorted(os.listdir(OLD_DIR)):
            if name.startswith(prefix):
                out.append(os.path.join(OLD_DIR, name))
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args(argv)

    log("=" * 74)
    log("Sauvegarde de INSTALLATION.fr.md")
    log("=" * 74)

    if not os.path.isfile(SOURCE):
        log("ERREUR : fichier source introuvable : %s" % SOURCE)
        return 2

    taille = os.path.getsize(SOURCE)
    if taille == 0:
        log("ERREUR : fichier source vide : %s" % SOURCE)
        return 2

    log("Source      : %s" % SOURCE)
    log("Taille      : %d octets" % taille)
    sha_source = sha256(SOURCE)
    log("SHA-256     : %s" % sha_source)

    if not args.force:
        existantes = deja_aujourdhui()
        if existantes:
            log("")
            log("PROTECTION : sauvegarde du jour deja existante :")
            for p in existantes:
                log("  - %s" % p)
            log("Refus. Utilisez --force pour forcer.")
            return 3

    os.makedirs(OLD_DIR, exist_ok=True)
    stamp = time.strftime("%Y%m%d_%H%M%S")
    dest = os.path.join(OLD_DIR, "INSTALLATION.fr_%s.md" % stamp)

    if os.path.exists(dest):
        log("ERREUR : destination existe deja : %s" % dest)
        return 4

    try:
        shutil.copy2(SOURCE, dest)
    except Exception as exc:
        log("ERREUR : copie impossible : %s" % exc)
        return 5

    log("")
    log("Copie creee : %s" % dest)
    log("Taille      : %d octets" % os.path.getsize(dest))
    sha_copie = sha256(dest)
    log("SHA-256     : %s" % sha_copie)

    if sha_copie != sha_source:
        log("ERREUR CRITIQUE : SHA-256 differs.")
        log("Original : %s" % sha_source)
        log("Copie    : %s" % sha_copie)
        return 6

    log("")
    log("VERDICT : sauvegarde VALIDE.")
    log("Vous pouvez maintenant reecrire INSTALLATION.fr.md.")
    log("=" * 74)
    return 0


if __name__ == "__main__":
    sys.exit(main())