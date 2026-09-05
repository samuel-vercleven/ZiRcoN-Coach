# ASTRA â€” ZiRcoN Coach Stable Base v1

Tu travailles sur ZiRcoN Coach.

## Mission
Stabiliser l'intÃ©gralitÃ© de l'existant AVANT toute nouvelle grosse feature.
La prochaine grosse feature prÃ©vue est le Build Optimizer, mais TU NE DOIS PAS l'implÃ©menter pendant cette mission.

## RÃ¨gles absolues
1. Ne supprime aucun fichier / module / comportement existant sans preuve, test et possibilitÃ© de rollback.
2. Pas de refactor massif "pour faire propre".
3. SÃ©parer autant que possible correction fonctionnelle et refactor architectural.
4. Toute modification de comportement doit Ãªtre couverte par un test.
5. Ne modifie jamais un rÃ©sultat attendu uniquement pour faire passer un test.
6. Conserve la compatibilitÃ© existante autant que possible.
7. Toute mÃ©trique douteuse doit Ãªtre marquÃ©e `EXPERIMENTAL`.
8. Aucun token Riot, secret ou `.env` sensible dans Git.
9. Travaille par petits changements logiques.
10. Avant chaque grosse modification, explique ce que tu vas changer et pourquoi.

## Documents obligatoires Ã  lire d'abord
- `TODO_STABILIZATION.md`
- `STABILIZATION_INVENTORY_TEMPLATE.md`
- `GOLDEN_GAMES_SPEC.md`
- `STABLE_BASE_EXIT_CHECKLIST.md`
- `FEATURE_PARKING_LOT.md`

## Ã‰tape 0 â€” Git / sauvegarde
Inspecte :
- `git status`
- branche
- commits rÃ©cents
- fichiers non trackÃ©s
- `.gitignore`

Si nÃ©cessaire, crÃ©er / confirmer un point de restauration prÃ©-stabilisation.
Ne fais aucune grosse modification avant l'audit.

## Ã‰tape 1 â€” Audit complet
Inspecte TOUT le repository et remplis `STABILIZATION_INVENTORY.md`.

Couvrir :
- Riot API
- Match loader
- Timeline loader
- Data Dragon
- cache
- parsers
- participants
- events
- frames
- items
- gold
- objectives
- rÃ´le
- metrics
- Death Analyzer
- aggregations
- reports
- rune knowledge
- item knowledge
- champion knowledge
- CLI
- scripts
- tests
- fixtures

Pour chaque module :
- rÃ´le
- entrÃ©es
- sorties
- dÃ©pendances
- tests
- statut
- bugs connus
- risque de rÃ©gression

Statuts uniquement :
- STABLE
- Ã€ VALIDER
- Ã€ CORRIGER
- EXPÃ‰RIMENTAL
- LEGACY
- NON UTILISÃ‰

Avant de modifier beaucoup de code, rends un rÃ©sumÃ© :
- ce qui est solide
- ce qui est fragile
- bugs probables
- duplications
- dette bloquante
- ordre de correction recommandÃ©

## Ã‰tape 2 â€” Golden Games
CrÃ©er / renforcer des tests de non-rÃ©gression Ã  partir de vraies games dÃ©jÃ  disponibles.

VÃ©rifier au minimum :
- champion
- rÃ´le
- durÃ©e
- victoire / dÃ©faite
- KDA
- CS
- morts
- timestamps de morts
- items finaux
- objectifs utiles

Ne mettre dans les valeurs attendues que des valeurs vÃ©rifiÃ©es.

## Ã‰tape 3 â€” Source de vÃ©ritÃ©
Identifier les zones oÃ¹ diffÃ©rents modules relisent diffÃ©remment les JSON Riot.

Cible conceptuelle :
```python
context.player
context.allies
context.enemies
context.timeline
context.events
context.items
context.gold
context.objectives
context.game_state
```

Si un GameContext existe : l'auditer et le renforcer.
Sinon : crÃ©er seulement le minimum utile, avec migration progressive et adapters de compatibilitÃ©.

## Ã‰tape 4 â€” Death Analyzer
PrioritÃ© de stabilisation.

VÃ©rifier :
- prÃ©cision temporelle des frames
- choix de frame autour de la mort
- interpolation Ã©ventuelle
- fenÃªtre avant / aprÃ¨s
- Ã©vÃ©nements attribuÃ©s Ã  la mort
- impact post-mort rÃ©el
- double comptage
- pseudo-rÃ©plication entre Ã©vÃ©nements d'une mÃªme game
- agrÃ©gations multi-games
- donnÃ©es incomplÃ¨tes

Corriger ou marquer expÃ©rimental.
Ajouter tests Golden Games.

## Ã‰tape 5 â€” Knowledge
### Runes
Valider IDs, noms, descriptions, nettoyage du texte, pertes d'information, comportement patch/version, tests.

### Items
PrÃ©parer la future base du Build Optimizer SANS dÃ©velopper l'optimizer.
SÃ©parer clairement :
```text
Raw Data Dragon
â†’ normalized item knowledge
â†’ futur scoring
```

VÃ©rifier :
- ID
- nom
- coÃ»t
- coÃ»t total
- composants
- transformations
- stats
- tags
- passifs
- disponibilitÃ© / items non achetables

### Champions
MÃªme principe : raw data sÃ©parÃ©e des connaissances utilisÃ©es par le raisonnement.

## Ã‰tape 6 â€” Robustesse
Tester les erreurs :
- Riot indisponible
- rate limit
- match invalide
- timeline absente
- participant introuvable
- rÃ´le ambigu
- item/rune/champion inconnu
- changement de patch
- None
- frame manquante
- timestamp hors limites

Aucun `except: pass` silencieux dangereux.

## Ã‰tape 7 â€” End-to-End
CrÃ©er / renforcer :
```text
Match
â†’ Timeline
â†’ Parsing
â†’ GameContext
â†’ Metrics
â†’ Death Analyzer
â†’ Knowledge
â†’ Report
```

ExÃ©cuter sur Golden Games puis petit batch rÃ©el.
Comparer avant / aprÃ¨s.

## Ã‰tape 8 â€” Fin
La mission est terminÃ©e uniquement lorsque `STABLE_BASE_EXIT_CHECKLIST.md` est honnÃªtement satisfaite.

Rendu final :
1. rÃ©sumÃ©
2. corrections
3. tests avant/aprÃ¨s
4. Golden Games
5. E2E
6. architecture rÃ©elle
7. risques restants
8. Go / No-Go pour `feature/build-optimizer`

Ne commence pas le Build Optimizer avant instruction explicite de Samuel.

