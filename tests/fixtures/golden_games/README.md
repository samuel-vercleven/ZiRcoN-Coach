# Seven real Golden Games

Expected facts were inspected from immutable local raw match/timeline JSON, then
cross-checked against independent normalized SQLite participant/event rows.
No analyzer output was used to define champion, role, result, KDA, CS, items or
death timestamps. Objective entries retain raw type/subtype/team, including HORDE
individual kills: they are not claimed to be independent strategic objectives.

Raw JSON and the consistent database snapshot remain ignored locally in
`logs/stabilization/snapshot/`. SHA-256 values in expected.json detect source drift.
On a different machine, missing real fixtures are an explicit failure of the real
audit, never a synthetic PASS. `python -m app.stabilization_snapshot` can extract
the selected local games if present; it never changes expected.json.

Cases: recent zero-death Shyvana, 11-death Viego, long Shyvana game, Support Zyra,
the frozen reset target, Magical Footwear grant, and undo/component-restore case.
Patches include 16.9, 16.16 and 16.17. No PUUID or raw player identity is committed.
