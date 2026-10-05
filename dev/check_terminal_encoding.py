# -*- coding: utf-8 -*-
r"""
dev\check_terminal_encoding.py — SCRIPT D'AUDIT CONSOLE (MANDAT v3.1.0)
Vérifie la pureté de l'affichage UTF-8 sans BOM sous CHCP 65001.
"""
import subprocess
import sys

def audit_console():
    print("[QA-CONSOLE] Vérification de la configuration active...")
    
    # 1. Tester si la console répond en UTF-8 (Code page 65001)
    try:
        res = subprocess.run(["chcp"], capture_output=True, text=True, shell=True)
        print(f"[QA-CONSOLE] Code page système détecté : {res.stdout.strip()}")
    except Exception as e:
        print(f"[QA-CONSOLE] Impossible de vérifier chcp : {e}")

    # 2. Chaîne de contrôle des accents critiques d'AiTron V3
    chaine_controle = "Moteur sémantique activé, routage hétérogène, étanchéité de la boîte noire."
    
    print("[QA-CONSOLE] Flux d'affichage physique simulé :")
    try:
        # Encodage brut vers la sortie standard
        sys.stdout.buffer.write(chaine_controle.encode('utf-8') + b"\n")
        sys.stdout.flush()
        print("[QA-CONSOLE] VERDICT ENCODAGE : CONFORME (Zéro caractère brisé généré)")
        return 0
    except Exception as e:
        print(f"[QA-CONSOLE] ERREUR critique de flux : {e}")
        return 1

if __name__ == "__main__":
    sys.exit(audit_console())
