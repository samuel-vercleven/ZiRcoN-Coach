# Stable Base v1 â€” Exit Checklist

## Git
- [x] snapshot prÃ©-stabilisation rÃ©cupÃ©rable
- [x] aucun secret commitÃ©

## Tests
- [x] unit tests OK
- [x] integration tests OK
- [x] Golden Games OK
- [x] end-to-end OK

## Data
- [x] parsing match fiable
- [x] parsing timeline fiable
- [x] timestamps cohÃ©rents
- [x] joueur correctement identifiÃ©
- [x] items/gold/objectives cohÃ©rents

## Death Analyzer
- [x] morts dÃ©tectÃ©es correctement
- [x] contexte temporel cohÃ©rent
- [x] impact post-mort validÃ© ou expÃ©rimental
- [x] pseudo-rÃ©plication contrÃ´lÃ©e
- [x] mÃ©triques douteuses isolÃ©es

## Knowledge
- [x] runes validÃ©es
- [x] items structurÃ©s pour la suite
- [x] champions suffisamment structurÃ©s
- [x] sÃ©paration raw / knowledge / scoring

## Architecture
- [x] GameContext dÃ©fini ou plan de migration documentÃ©
- [x] duplications critiques connues
- [x] interfaces majeures comprÃ©hensibles

## Robustesse
- [x] erreurs explicites
- [x] donnÃ©es manquantes gÃ©rÃ©es
- [x] logs suffisants

## Go Build Optimizer
GO seulement si :
- aucune entrÃ©e critique connue comme fausse
- Golden Games fiables
- Death Analyzer n'introduit pas de rÃ©sultats trompeurs non marquÃ©s
- Item Knowledge suffisamment propre

## Disposition de la stabilisation — 2026-09-06

Les cases cochées décrivent le périmètre vérifié, pas une validation universelle
sur tous les patches. Voir STABILIZATION_REPORT.md : 43/43 suites, 22 nouveaux
tests, 7 Golden Games, 680 morts réelles, 89 fichiers FROZEN inchangés.

REVIEW_REQUIRED pour le périmètre du tag stable-base-v1 : l'audit Phase 2D sur
latest 16.17 refuse correctement les ratios pinnés 16.16 ; le replay exact
16.16.1 passe. NO-GO pour un optimizer générique sur le patch courant.
Aucun freeze ni Build Optimizer n'a été démarré.

