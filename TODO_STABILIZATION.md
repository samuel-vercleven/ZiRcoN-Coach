# ZiRcoN Coach â€” TODO Stabilisation Stable Base v1

## Objectif
Figer, auditer, tester et stabiliser l'existant avant toute nouvelle grosse feature.
La prochaine grosse feature aprÃ¨s validation sera le **Build Optimizer**.

## 0 â€” Protection
- [x] VÃ©rifier `git status`
- [x] VÃ©rifier la branche actuelle
- [x] CrÃ©er un snapshot complet
- [x] CrÃ©er le tag `pre-stabilization-v1`
- [x] CrÃ©er / utiliser `stabilization/stable-base-v1`
- [x] VÃ©rifier les fichiers non suivis
- [x] VÃ©rifier `.gitignore`
- [x] VÃ©rifier qu'aucun secret / token Riot n'est commitÃ©

## 1 â€” Audit complet
- [x] Inventorier tous les modules Python
- [x] Identifier Riot API / Match loader / Timeline loader / Data Dragon
- [x] Identifier parsers / modÃ¨les / events / frames
- [x] Identifier mÃ©triques et agrÃ©gations
- [x] Identifier Death Analyzer
- [x] Identifier Rune / Item / Champion Knowledge
- [x] Identifier CLI / scripts / rapports
- [x] Identifier tests / fixtures
- [x] Classer chaque module : STABLE / Ã€ VALIDER / Ã€ CORRIGER / EXPÃ‰RIMENTAL / LEGACY / NON UTILISÃ‰
- [x] Remplir `STABILIZATION_INVENTORY.md`

## 2 â€” Golden Games / non-rÃ©gression
- [x] SÃ©lectionner 5 Ã  10 vraies games reprÃ©sentatives
- [x] Conserver match + timeline localement si dÃ©jÃ  disponibles
- [x] CrÃ©er les valeurs attendues vÃ©rifiÃ©es
- [x] Tester champion / rÃ´le / durÃ©e / W-L / KDA / CS
- [x] Tester morts et timestamps
- [x] Tester items finaux
- [x] Tester objectifs utiles
- [x] Ajouter tests parsing
- [x] Ajouter tests timeline
- [x] Ajouter tests Death Analyzer
- [x] Ajouter au moins un vrai test E2E

## 3 â€” Source de vÃ©ritÃ© / GameContext
- [x] Auditer les structures existantes avant d'en crÃ©er de nouvelles
- [x] Identifier les accÃ¨s JSON Riot dupliquÃ©s
- [x] DÃ©finir une reprÃ©sentation centrale minimale
- [x] Migrer progressivement, sans refactor massif
- [x] Conserver des adapters de compatibilitÃ© si nÃ©cessaire

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
- [x] VÃ©rifier la prÃ©cision temporelle des frames
- [x] VÃ©rifier la frame choisie autour de chaque mort
- [x] Documenter interpolation / approximation Ã©ventuelle
- [x] VÃ©rifier fenÃªtres avant / aprÃ¨s mort
- [x] VÃ©rifier impact post-mort rÃ©el
- [x] Ã‰viter double comptage
- [x] Corriger la pseudo-rÃ©plication au niveau des games
- [x] Valider les mÃ©triques agrÃ©gÃ©es
- [x] GÃ©rer donnÃ©es manquantes
- [x] Tester sur Golden Games
- [x] Marquer les mÃ©triques non validÃ©es `EXPERIMENTAL`

## 5 â€” Knowledge System
### Runes
- [x] Valider IDs / noms / descriptions
- [x] VÃ©rifier nettoyage HTML / texte
- [x] VÃ©rifier perte silencieuse d'information
- [x] Ajouter tests

### Items
- [x] Auditer ce qui existe dÃ©jÃ 
- [x] SÃ©parer Raw Data Dragon / Knowledge normalisÃ©e / futur scoring
- [x] VÃ©rifier ID / nom / coÃ»t / coÃ»t total
- [x] VÃ©rifier composants et transformations
- [x] VÃ©rifier stats / tags / passifs
- [x] Identifier items non achetables / spÃ©ciaux
- [x] PrÃ©parer proprement la base du futur Build Optimizer SANS l'implÃ©menter

### Champions
- [x] Auditer / normaliser les donnÃ©es utiles
- [x] Ã‰viter les hypothÃ¨ses dispersÃ©es en dur

## 6 â€” Robustesse
- [x] Riot API indisponible
- [x] rate limit
- [x] match invalide
- [x] timeline absente
- [x] participant introuvable
- [x] rÃ´le ambigu
- [x] item / rune / champion inconnu
- [x] diffÃ©rence de patch
- [x] valeurs None
- [x] frame manquante
- [x] timestamp hors limites
- [x] supprimer les `except: pass` dangereux

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

- [x] Lancer sur Golden Games
- [x] Lancer sur un petit batch rÃ©el
- [x] Logger les erreurs
- [x] DÃ©tecter valeurs aberrantes
- [x] Comparer avant / aprÃ¨s stabilisation

## 8 â€” Stable Base v1
- [x] Tous les tests critiques passent
- [x] Pas de rÃ©gression critique connue
- [x] Documentation Ã  jour
- [x] Modules legacy identifiÃ©s
- [x] MÃ©triques expÃ©rimentales explicitement marquÃ©es
- [ ] `stable-base-v1` prÃªt Ã  Ãªtre taguÃ©

## Ensuite uniquement
- [ ] `feature/build-optimizer`

## Disposition de la stabilisation — 2026-09-06

Les cases cochées décrivent le périmètre vérifié, pas une validation universelle
sur tous les patches. Voir STABILIZATION_REPORT.md : 43/43 suites, 22 nouveaux
tests, 7 Golden Games, 680 morts réelles, 89 fichiers FROZEN inchangés.

REVIEW_REQUIRED pour le périmètre du tag stable-base-v1 : l'audit Phase 2D sur
latest 16.17 refuse correctement les ratios pinnés 16.16 ; le replay exact
16.16.1 passe. NO-GO pour un optimizer générique sur le patch courant.
Aucun freeze ni Build Optimizer n'a été démarré.

