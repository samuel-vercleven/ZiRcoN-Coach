# ZiRcoN Coach â€” Golden Games

Objectif : crÃ©er un corpus de rÃ©fÃ©rence pour dÃ©tecter les rÃ©gressions.

Cible : 5 Ã  10 games reprÃ©sentatives.

Structure recommandÃ©e :
```text
tests/
  fixtures/
    golden_games/
      <match_id>/
        match.json
        timeline.json
        expected.json
```

Valeurs possibles dans `expected.json` :
- champion
- rÃ´le
- win/loss
- durÃ©e
- K/D/A
- CS
- timestamps de morts
- items finaux
- objectifs vÃ©rifiÃ©s

RÃ¨gles :
- Ne renseigner que des valeurs rÃ©ellement vÃ©rifiÃ©es.
- Ne jamais changer un attendu uniquement pour faire passer un test.
- Une modification d'attendu doit Ãªtre justifiÃ©e.

