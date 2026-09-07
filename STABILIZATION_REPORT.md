# Stable Base v1 — bilan de stabilisation

Date : 2026-09-07. Branche : `stabilization/stable-base-v1`.

## Verdict

**Corrections techniques : PASS. Revue de périmètre : REVIEW_REQUIRED.**
Pas de tag `stable-base-v1`, pas de freeze autonome, pas de Build Optimizer.
NO-GO pour un optimizer générique sur le patch courant sans contrat explicite
d'admissibilité des entrées. Les données incomplètes restent exclues ou signalées,
elles ne deviennent pas des faits exécutables parce que les tests passent.

## Protection et inventaire

- Référence : `ca119d1ed304594345ae17c09dbadff142fb5f5f`, tag `pre-stabilization-v1`.
- Archive des sources suivies, sauvegarde SQLite cohérente et sept paires JSON
  conservées localement dans `logs/stabilization/snapshot/`, ignoré par Git.
  Secrets, environnement Python et caches régénérables exclus de l'archive source.
- 159 modules Python inventoriés dans `STABILIZATION_INVENTORY.md` ; statuts
  limités au périmètre vérifié, modules legacy et accès SQL directs identifiés.
- 89 fichiers FROZEN inchangés contre le tag de restauration, y compris les
  modifications éventuellement déjà committées. `main.py` est inchangé.
- La suppression locale de `TODO.md`, constatée au début de cette reprise,
  reste une modification utilisateur exclue des commits. Le pack fourni
  `TODO_STABILIZATION.md` définit cette mission.

## Corrections et compatibilité

1. Cache de rapports indexé par joueur + match + analyzer + version. Table
   additive, aucune ligne legacy supprimée. L'UI ne lit plus les rapports non
   attribuables au compte actif ; un cache JSON malformé produit ERROR.
2. `GameContext` valide participant, rôle/opposant, timeline, frames, timestamps,
   ressources manquantes et nombre de morts brutes. Les rapports refusent les
   entrées invalides. Une sortie v11 vide ne prouve plus l'absence de mort.
3. Une exception de dépendance n'est plus assimilée à une donnée vide valide.
   Les nombres de rapports générés et de parties analysées sont distingués.
4. NULL KDA/CS/durée/résultat n'est plus transformé en zéro ou défaite. Les
   agrégats concernés restent indisponibles, les graphiques gardent leurs trous.
5. Les séquences d'objectifs d'équipe ne sont plus promues en sévérité personnelle.
   Les ressources Death sont des observations sur une fenêtre de frames ; leur
   interprétation est EXPERIMENTAL, y compris dans la synthèse coach.
6. Les intervalles d'inventaire ambigus et les catalogues de patch incompatible
   rendent la présentation Build PARTIAL. Le statut brut `final_validation`
   est conservé distinctement, même lorsqu'il vaut EXACT.
7. Le profil/rang mis en cache survit à une panne API et n'est pas annoncé CURRENT
   à tort. Les statuts sync legacy globaux ne sont pas attribués au nouveau compte,
   y compris avant sa première partie locale ou la résolution de son identité.
8. Réponses API de forme invalide, mauvaise queue/identité et timelines invalides
   sont rejetées avant ingestion. Pas de sync vers une DB alternative implicite.
9. Clé entièrement masquée, paramètres JSON non-objet tolérés sans crash,
   chemins d'assets confinés. Les erreurs worker n'affirment plus à tort que
   toutes les étapes ont été annulées.
10. Une DB corrompue n'est pas remplacée à l'ouverture : état indisponible et
    accès aux réglages conservé. Cartes Qt retirées immédiatement, badges non
    étirés, textes de sync bornés et réglages scrollables à taille minimale.

Présentation finale : Death/Tempo/Objectifs/Build adapter v4, Reset adapter v3.
Ces versions ne changent pas les versions ni le comportement des sources FROZEN.

## Tests avant / après

| Vérification | Avant | Après |
|---|---:|---:|
| Suites de commandes de régression, dont main.py | 41/41 | 43/43 |
| Nouvelles régressions unittest ciblées | 0 | 22/22 |
| Golden Games E2E persistées | 0 | 7/7 |
| Compilation Python exhaustive finale | — | 159 modules |
| Fichiers FROZEN comparés au tag | 89 inchangés | 89 inchangés |

Ces nombres sont des **suites de commandes**, pas un total inventé des milliers
d'assertions internes des anciens scripts. Trois régressions initiales ont
reproduit les défauts avant correction. Les tests suivants couvrent cache,
scoping, API, None, données manquantes, dates, UI, isolation historique et
déduplication des objectifs entre fenêtres de morts chevauchantes.

Audits knowledge réels : **21/22 commandes par défaut PASS**. La commande Phase 2D
sur latest `16.17.1` renvoie correctement REVIEW_REQUIRED : ratios pinnés en
`16.16`, 0/173 admis sur le patch incompatible, 2 907 lignes AS non résolues.
Le contrôle séparé de la baseline **16.16.1 PASS** : 173/173 ratios, 3 114 lignes
standard, zéro blocking/review. Aucun attendu n'a été affaibli et aucun échec
latest n'a été effacé du journal.

Les tests Alpha existants, l'audit V0.1 et le contrôle de parité sur cinq matchs
réels passent. Ce dernier mesure la parité du cache, pas une couverture sémantique
indépendante : son ancien affichage tautologique `N/N mapped` a été corrigé.

## Golden Games et batch réel

- Sept matchs réels : zéro mort, onze morts, partie longue, rôle Support,
  cible Reset, Magical Footwear et undo/restauration de composant ; patches
  16.9, 16.16 et 16.17. Données brutes locales, SHA-256 et attendus dans Git.
- Identité/champion/rôle/durée/résultat/KDA/CS/items, événements et morts
  comparés aux données brutes et à la projection SQL. **33 morts, 35 rapports**.
- Les événements HORDE individuels restent des événements bruts, pas des
  objectifs stratégiques indépendants inventés.
- Six reconstructions finales v22 sont EXACT ou EXACT_WITH_EXPLAINED_GRANT.
  `EUW1_7959361127` reste PARTIAL : item Riot final `3871` manquant dans la
  reconstruction. Cette limite vérifiée est désormais une assertion explicite.
- Tout l'historique local : **118 matchs, 680 morts brutes = 680 morts v11**,
  aucune entrée signalée invalide sur ce corpus, aucune mort non mesurable.
- Vingt matchs récents : **100 rapports** ; Death 20 AVAILABLE ; trois analyzers
  Jungle 18 AVAILABLE + 2 UNAVAILABLE chacun ; Build 2 AVAILABLE + 18 PARTIAL.
  Badges globaux : **1 AVAILABLE / 19 PARTIAL**. La précision prime sur la couverture.

## Pipeline réel

```text
Match ID + compte
  -> SQLite : Match / Timeline bruts
  -> GameContext : admission des données, inconnus explicites
  -> readers SQL et analyzers FROZEN : mesures historiques / preuves
  -> knowledge par patch : faits conservés, pas de scoring d'items
  -> adapters : provenance, fiabilité et EXPERIMENTAL
  -> cache par joueur et version -> ViewModels -> desktop PySide6
```

Les readers existants ne sont pas remplacés : GameContext est une frontière
minimale d'admission. Les accès directs legacy restent identifiés, pas supprimés.
La séparation raw / knowledge / éventuel scoring futur est conservée.

## Death et limites Riot

- Dernière frame <= mort, première frame strictement > mort ; pas d'interpolation.
- `*_cost_60` est un ancien nom de fenêtre encadrante, pas exactement +60 secondes.
- Actions pré-mort, fenêtres chevauchantes, chaînes et événements d'équipe ne
  prouvent ni coût causal, ni faute, ni perte nette additive.
- v11 ajoute l'historique par match entier ; tests same-game/future-game ajoutés.
  Les statistiques d'issue sont au niveau match et dédupliquent les objectifs.
- Runes, descriptions d'items/champions et fragments numériques sont des faits
  sourcés, pas des formules de gameplay exécutables. UNKNOWN/UNRESOLVED restent.
- L'AS 16.17 n'est pas résolue par une source 16.16. Le zero-gate Phase 2I reste
  fermé : aucun owner promu, aucun moteur de combat ou arithmetic stat-scaling.

## Validation desktop et limites de cette exécution

`python run_app.py` a réellement ouvert la fenêtre native ZiRcoN Coach, puis a
été fermé proprement (code 0). 22 captures natives produites aux tailles
1400×850 et 1100×700 ; Dashboard, Historique, Post-game, Progression et Réglages
inspectés. Les tests offscreen restent distincts de cette vérification native.
Pas de validation live de clé Riot ni de sync Riot dans cette stabilisation :
les erreurs/credentials/sync ont été testés avec mocks ; les catalogues publics
Data Dragon ont réellement été chargés. Aucune clé affichée ou committée.

## Revue et suite autorisée

Revoir le périmètre acceptable pour `stable-base-v1`, en particulier la distinction
baseline gelée/current patch et la fiabilité des états intermédiaires Build.
Les fixtures brutes restent locales : leur absence ailleurs fait échouer
l'audit réel explicitement, elle ne produit pas un PASS synthétique.
Les anciens readers/projections et helpers latest sont conservés, avec risque
documenté pour tout futur consommateur direct. Aucun refactor massif effectué.
`feature/build-optimizer` reste en parking ; ce rapport ne l'autorise pas.
