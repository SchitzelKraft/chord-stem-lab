# Chord detection A/B — `Example.mp3`

_Generated 2026-04-18T19:34:04 — first 3 chord changes per mix._

**Expected sequence** (3): `D` `Em` `A`

## Model: `chordino`

| # | expected | original | bass+other | bass+vocals | vocals+other | bass+vocals+other |
|---|---|---|---|---|---|---|
| 1 | `D` | `D` | `D` | `D7` | `D` | `D` |
| 2 | `Em` | `Em7` | `G` | `E` | `Em7` | `G` |
| 3 | `A` | `D6` | `A` | `A7` | `Bm` | `D` |

**Match vs expected (exact / same-root):**

- `original`: 1/3 exact, 2/3 same-root
- `bass+other`: 2/3 exact, 2/3 same-root  ← best
- `bass+vocals`: 0/3 exact, 3/3 same-root
- `vocals+other`: 1/3 exact, 2/3 same-root
- `bass+vocals+other`: 1/3 exact, 1/3 same-root

## Model: `madmom`

| # | expected | original | bass+other | bass+vocals | vocals+other | bass+vocals+other |
|---|---|---|---|---|---|---|
| 1 | `D` | `D` | `D` | `Dm` | `D` | `D` |
| 2 | `Em` | `Em` | `Em` | `A` | `G` | `G` |
| 3 | `A` | `A` | `A` | `Em` | `A` | `A` |

**Match vs expected (exact / same-root):**

- `original`: 3/3 exact, 3/3 same-root  ← best
- `bass+other`: 3/3 exact, 3/3 same-root  ← best
- `bass+vocals`: 0/3 exact, 1/3 same-root
- `vocals+other`: 2/3 exact, 2/3 same-root
- `bass+vocals+other`: 2/3 exact, 2/3 same-root

## Model: `ismir2019`

| # | expected | original | bass+other | bass+vocals | vocals+other | bass+vocals+other |
|---|---|---|---|---|---|---|
| 1 | `D` | `D` | `D` | `E` | `D` | `D` |
| 2 | `Em` | `Em` | `Em` | `Bm` | `Em` | `Em` |
| 3 | `A` | `A` | `A` | `G` | `A` | `A` |

**Match vs expected (exact / same-root):**

- `original`: 3/3 exact, 3/3 same-root  ← best
- `bass+other`: 3/3 exact, 3/3 same-root  ← best
- `bass+vocals`: 0/3 exact, 0/3 same-root
- `vocals+other`: 3/3 exact, 3/3 same-root  ← best
- `bass+vocals+other`: 3/3 exact, 3/3 same-root  ← best
