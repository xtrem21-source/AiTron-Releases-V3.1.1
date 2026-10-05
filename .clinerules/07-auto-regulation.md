# Règle 07 — Auto-régulation

## Principe
Un mandat trop lourd ne doit jamais planter ou être bâclé.
Tu es AUTORISÉ à subdiviser pour préserver la qualité.

## Règles actionnables

### 1. Subdivision d'un mandat trop lourd

Si la charge d'un mandat dépasse ta capacité en un seul passage :
- Tu es AUTORISÉ à subdiviser en sous-étapes internes
- Tu documentes ce choix dans dev\DECISIONS.md
- Tu livres chaque sous-étape AVANT de passer à la suivante
- Tu appliques la doctrine transactionnelle à chaque sous-étape

### 2. Détection de surcharge

Tu dois subdiviser si :
- Le mandat contient plus de 3 étapes majeures indépendantes
- Le mandat touche à plus de 2 composants critiques
- Tu estimes que la fenêtre de contexte sera saturée
- Tu détectes un risque de régression

### 3. Problème de conception dans le mandat

Si tu détectes un problème de conception :
- Tu le signales AVANT d'exécuter
- Tu proposes une alternative
- Tu attends la validation

### 4. Limite de contexte atteinte

Si tu atteins une limite de contexte :
- Tu t'arrêtes sur un état vérifié et cohérent
- Tu documentes où tu en es dans dev\patch_integrity.log
- Tu mets à jour le Memory Bank
- Tu signales qu'une reprise est nécessaire

## Format de décision d'auto-régulation

Quand tu subdivises, tu ajoutes une entrée dans dev\DECISIONS.md :

## D-XXX — Auto-régulation : subdivision du mandat vX.Y.Z
**Contexte** : mandat trop lourd pour un seul passage
**Décision** : subdivision en vX.Y.Za, vX.Y.Zb, vX.Y.Zc
**Justification** : surfaces disjointes, isolation des régressions
**Conséquences** : livraison séquentielle, validation à chaque étape

## Exemples de subdivision réussie

### Exemple 1 — v1.7.0 (Quantization + PII)
- v1.7.0a : Quantization locale
- v1.7.0b : Filtre PII
- Validation à chaque sous-étape

### Exemple 2 — v1.9.0 → v2.1.0 (Cascade)
- v1.9.0 : Speculative Decoding
- v2.0.0a : Espace hermétique
- v2.0.0b : Profil apprenant
- v2.1.0a : Découverte réseau
- v2.1.0b : Routage fédéré
- Validation à chaque sous-étape

### Exemple 3 — v1.5.0 (Vision + MCP)
- v1.5.0a : Vision locale
- v1.5.0b : Protocole MCP
- Validation à chaque sous-étape

## Ce qu'il ne faut PAS faire

- Ne JAMAIS bâcler une étape pour finir plus vite
- Ne JAMAIS ignorer la doctrine transactionnelle pour gagner du temps
- Ne JAMAIS livrer un état intermédiaire cassé
- Ne JAMAIS mentir sur l'avancement

## Interdictions
- Ne jamais planter par surcharge
- Ne jamais bâcler par précipitation
- Ne jamais cacher une subdivision
- Ne jamais oublier de documenter une auto-régulation
