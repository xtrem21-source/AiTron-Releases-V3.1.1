# Security — AiTron V3

## Perimetre
AiTron V3 est un outil local-first. Rien n'est envoye vers l'exterieur par defaut.

## Ce qui est protege
### Filtre PII (best-effort)
- 3 niveaux : regex + entropie + NER local
- Masquage reversible [PII-TYPE-n]
- Audit dans dev\crash.log
- Desactivable : --no-pii-filter

### Espace hermetique
- AES-256-GCM (authentifie)
- Cle derivee PBKDF2 (jamais stockee)
- Anti-perte (verification avant suppression)

### Local-first
- Par defaut : tout reste local
- Cloud : uniquement si cles API configurees

## Ce qui n'est PAS protege
- Rendu navigateur (IHM web)
- Effacement RAM (GC Python)
- Mot de passe oublie = donnees perdues
- Vol physique du PC allume

## Bonnes pratiques
1. Mot de passe fort pour le vault
2. Ne pas partager config\cloud-keys.env
3. Auditer dev\crash.log
4. Mettre a jour les binaires
5. Desactiver le filtre PII uniquement si legitime

## Signaler une faille
Documenter dans dev\crash.log (categorie SECURITY), puis contacter le mainteneur.

## Licence
MIT. Fork de LocalAI. Non affilie au projet officiel.
