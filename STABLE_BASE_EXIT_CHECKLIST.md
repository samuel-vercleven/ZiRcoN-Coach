# Stable Base v1 â€” Exit Checklist

## Git
- [ ] snapshot prÃ©-stabilisation rÃ©cupÃ©rable
- [ ] aucun secret commitÃ©

## Tests
- [ ] unit tests OK
- [ ] integration tests OK
- [ ] Golden Games OK
- [ ] end-to-end OK

## Data
- [ ] parsing match fiable
- [ ] parsing timeline fiable
- [ ] timestamps cohÃ©rents
- [ ] joueur correctement identifiÃ©
- [ ] items/gold/objectives cohÃ©rents

## Death Analyzer
- [ ] morts dÃ©tectÃ©es correctement
- [ ] contexte temporel cohÃ©rent
- [ ] impact post-mort validÃ© ou expÃ©rimental
- [ ] pseudo-rÃ©plication contrÃ´lÃ©e
- [ ] mÃ©triques douteuses isolÃ©es

## Knowledge
- [ ] runes validÃ©es
- [ ] items structurÃ©s pour la suite
- [ ] champions suffisamment structurÃ©s
- [ ] sÃ©paration raw / knowledge / scoring

## Architecture
- [ ] GameContext dÃ©fini ou plan de migration documentÃ©
- [ ] duplications critiques connues
- [ ] interfaces majeures comprÃ©hensibles

## Robustesse
- [ ] erreurs explicites
- [ ] donnÃ©es manquantes gÃ©rÃ©es
- [ ] logs suffisants

## Go Build Optimizer
GO seulement si :
- aucune entrÃ©e critique connue comme fausse
- Golden Games fiables
- Death Analyzer n'introduit pas de rÃ©sultats trompeurs non marquÃ©s
- Item Knowledge suffisamment propre

