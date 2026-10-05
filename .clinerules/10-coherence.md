# Regle 10 - Coherence charte / projet

## Principe
Avant de demarrer un projet, tu verifies la coherence charte / projet.
Tu presentes une CHECKLIST a l'utilisateur. Tu attends son GO avant d'executer.

## Etape 1 - Verification de coherence (6 points)

Avant toute action, tu verifies :
1. Langage / technologie
2. Format de sortie (script, exe, binaire)
3. Mode de distribution (local, service, app)
4. Utilisateurs (mono, multi)
5. Architecture (monolithique, modulaire)
6. Contraintes specifiques (Docker, WSL, etc.)

## Etape 2 - Checklist a presenter

Tu presentes a l'utilisateur une checklist du type :

    =====================================================================
      CHECKLIST DE DEMARRAGE - AiTron V3
    =====================================================================

    Verification de coherence charte / projet :

      [OK] Langage          : Python (install_AiTron_v3.py)
      [OK] Format sortie    : Arborescence portable (LocalAI Windows)
      [OK] Distribution     : Locale, portable, cle USB
      [OK] Utilisateurs     : Mono-utilisateur
      [OK] Architecture     : Modulaire (backends separes)
      [OK] Contraintes      : Pas de Docker, pas de WSL

    Plan d'action :
      1. Lire la charte et le Memory Bank
      2. Verifier l'etat actuel du projet
      3. Implementer les fonctionnalites du mandat en cours
      4. Tester en conditions physiques
      5. Documenter (CHANGELOG, DECISIONS, etc.)
      6. Commit + tag Git

    Point d'attention : (a completer selon le mandat en cours)

    =====================================================================
      Tapez GO pour demarrer, ou signalez une anomalie.
    =====================================================================

## Etape 3 - Attente du GO

Tu attends que l'utilisateur tape GO (ou equivalent).
Tu ne commences PAS avant.

Si l'utilisateur signale une anomalie :
- Tu documentes dans dev/DECISIONS.md
- Tu proposes des alternatives
- Tu attends une nouvelle validation

## Si une incoherence est detectee

Tu ne fonces PAS. Tu fais ceci :
1. Tu signales l'incoherence dans la checklist
2. Tu decris ce qui ne correspond pas
3. Tu proposes 2 ou 3 alternatives
4. Tu attends la validation

## Format de signalement

    ## A-XXX - Incoherence charte / projet
    **Detecte le** : AAAAMMJJ_HHMMSS
    **Section de la charte** : (ex. Section 0.4)
    **Incoherence** : (description)
    **Impact** : (consequence)
    **Alternatives proposees** :
      1. ...
      2. ...
      3. ...
    **Recommandation** : ...
    **Statut** : EN ATTENTE

## Interdictions
- Ne jamais ignorer une incoherence
- Ne jamais forcer une charte inadaptee
- Ne jamais demarrer sans avoir obtenu le GO explicite
