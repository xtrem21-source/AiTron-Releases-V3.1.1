# Règle 04 — Structure du projet

## Principe
Arborescence ouverte, modulaire, portable.

## Structure de la sandbox

<sandbox>\
├── CHARTE.md                    (loi constitutionnelle)
├── JOURNAL.md                   (journal narratif)
├── PERIMETRE.md                 (contrat de confinement)
├── INSTALLATION.md              (guide utilisateur)
├── ANOMALIES_NON_RÉSOLUES.log   (état des anomalies)
├── install_AiTron_v3.py         (installeur maître)
├── MANDAT-*.md                  (mandats en cours)
├── Installeur\                  (boîte noire)
├── dev\                         (espace libre, à plat)
│   ├── CHANGELOG.md
│   ├── DECISIONS.md
│   ├── patch_integrity.log
│   ├── crash.log
│   ├── BETA_TEST_REPORT.md
│   └── old\                     (mise à l'écart)
├── log\                         (traces techniques)
├── build\                       (toolchain, sources)
└── AiTron\                      (produit déployé)

## Règles actionnables

1. La sandbox est détectée dynamiquement :
   - Priorité 1 : --root <chemin>
   - Priorité 2 : dossier du script
   - Jamais de chemin en dur

2. Le produit déployé est dans <sandbox>\AiTron\
   - Effaçable
   - Reconstructible par install_AiTron_v3.py

3. La boîte noire est dans <sandbox>\Installeur\
   - Écriture contrôlée (uniquement via archive_installer())

4. Le laboratoire est dans <sandbox>\dev\
   - À plat (sauf old\)
   - old\ : tout ce qu'on met de côté

## Interdictions
- Ne jamais écrire hors de la sandbox
- Ne jamais créer de sous-dossiers dans dev\ (sauf old\)
- Ne jamais mettre un chemin en dur
- Ne jamais modifier AiTron\ manuellement
