# ZiRcoN Coach â€” TODO Stabilisation Stable Base v1

## Objectif
Figer, auditer, tester et stabiliser l'existant avant toute nouvelle grosse feature.
La prochaine grosse feature aprÃ¨s validation sera le **Build Optimizer**.

## 0 â€” Protection
- [ ] VÃ©rifier `git status`
- [ ] VÃ©rifier la branche actuelle
- [ ] CrÃ©er un snapshot complet
- [ ] CrÃ©er le tag `pre-stabilization-v1`
- [ ] CrÃ©er / utiliser `stabilization/stable-base-v1`
- [ ] VÃ©rifier les fichiers non suivis
- [ ] VÃ©rifier `.gitignore`
- [ ] VÃ©rifier qu'aucun secret / token Riot n'est commitÃ©

## 1 â€” Audit complet
- [ ] Inventorier tous les modules Python
- [ ] Identifier Riot API / Match loader / Timeline loader / Data Dragon
- [ ] Identifier parsers / modÃ¨les / events / frames
- [ ] Identifier mÃ©triques et agrÃ©gations
- [ ] Identifier Death Analyzer
- [ ] Identifier Rune / Item / Champion Knowledge
- [ ] Identifier CLI / scripts / rapports
- [ ] Identifier tests / fixtures
- [ ] Classer chaque module : STABLE / Ã€ VALIDER / Ã€ CORRIGER / EXPÃ‰RIMENTAL / LEGACY / NON UTILISÃ‰
- [ ] Remplir `STABILIZATION_INVENTORY.md`

## 2 â€” Golden Games / non-rÃ©gression
- [ ] SÃ©lectionner 5 Ã  10 vraies games reprÃ©sentatives
- [ ] Conserver match + timeline localement si dÃ©jÃ  disponibles
- [ ] CrÃ©er les valeurs attendues vÃ©rifiÃ©es
- [ ] Tester champion / rÃ´le / durÃ©e / W-L / KDA / CS
- [ ] Tester morts et timestamps
- [ ] Tester items finaux
- [ ] Tester objectifs utiles
- [ ] Ajouter tests parsing
- [ ] Ajouter tests timeline
- [ ] Ajouter tests Death Analyzer
- [ ] Ajouter au moins un vrai test E2E

## 3 â€” Source de vÃ©ritÃ© / GameContext
- [ ] Auditer les structures existantes avant d'en crÃ©er de nouvelles
- [ ] Identifier les accÃ¨s JSON Riot dupliquÃ©s
- [ ] DÃ©finir une reprÃ©sentation centrale minimale
- [ ] Migrer progressivement, sans refactor massif
- [ ] Conserver des adapters de compatibilitÃ© si nÃ©cessaire

Cible :
```text
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

## 4 â€” Death Analyzer
- [ ] VÃ©rifier la prÃ©cision temporelle des frames
- [ ] VÃ©rifier la frame choisie autour de chaque mort
- [ ] Documenter interpolation / approximation Ã©ventuelle
- [ ] VÃ©rifier fenÃªtres avant / aprÃ¨s mort
- [ ] VÃ©rifier impact post-mort rÃ©el
- [ ] Ã‰viter double comptage
- [ ] Corriger la pseudo-rÃ©plication au niveau des games
- [ ] Valider les mÃ©triques agrÃ©gÃ©es
- [ ] GÃ©rer donnÃ©es manquantes
- [ ] Tester sur Golden Games
- [ ] Marquer les mÃ©triques non validÃ©es `EXPERIMENTAL`

## 5 â€” Knowledge System
### Runes
- [ ] Valider IDs / noms / descriptions
- [ ] VÃ©rifier nettoyage HTML / texte
- [ ] VÃ©rifier perte silencieuse d'information
- [ ] Ajouter tests

### Items
- [ ] Auditer ce qui existe dÃ©jÃ 
- [ ] SÃ©parer Raw Data Dragon / Knowledge normalisÃ©e / futur scoring
- [ ] VÃ©rifier ID / nom / coÃ»t / coÃ»t total
- [ ] VÃ©rifier composants et transformations
- [ ] VÃ©rifier stats / tags / passifs
- [ ] Identifier items non achetables / spÃ©ciaux
- [ ] PrÃ©parer proprement la base du futur Build Optimizer SANS l'implÃ©menter

### Champions
- [ ] Auditer / normaliser les donnÃ©es utiles
- [ ] Ã‰viter les hypothÃ¨ses dispersÃ©es en dur

## 6 â€” Robustesse
- [ ] Riot API indisponible
- [ ] rate limit
- [ ] match invalide
- [ ] timeline absente
- [ ] participant introuvable
- [ ] rÃ´le ambigu
- [ ] item / rune / champion inconnu
- [ ] diffÃ©rence de patch
- [ ] valeurs None
- [ ] frame manquante
- [ ] timestamp hors limites
- [ ] supprimer les `except: pass` dangereux

## 7 â€” End-to-End
Pipeline cible :
```text
Match ID
â†’ Match loader
â†’ Timeline loader
â†’ Parser
â†’ GameContext
â†’ Metrics
â†’ Death Analyzer
â†’ Knowledge
â†’ Report
```

- [ ] Lancer sur Golden Games
- [ ] Lancer sur un petit batch rÃ©el
- [ ] Logger les erreurs
- [ ] DÃ©tecter valeurs aberrantes
- [ ] Comparer avant / aprÃ¨s stabilisation

## 8 â€” Stable Base v1
- [ ] Tous les tests critiques passent
- [ ] Pas de rÃ©gression critique connue
- [ ] Documentation Ã  jour
- [ ] Modules legacy identifiÃ©s
- [ ] MÃ©triques expÃ©rimentales explicitement marquÃ©es
- [ ] `stable-base-v1` prÃªt Ã  Ãªtre taguÃ©

## Ensuite uniquement
- [ ] `feature/build-optimizer`

