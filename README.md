# Chord Stem Lab

Compare automatic chord detection on the **original mix** versus **re-mixed stem combinations** from [Demucs](https://github.com/facebookresearch/demucs). Useful for A/B experiments: does removing drums (or other stems) change what Chordino, Madmom, or an ISMIR2019-style model hears in the opening bars?

## What it does

1. **Separate** the track with Demucs (`htdemucs_ft` by default).
2. **Build mixes**: original, and sums like `bass+other`, `bass+vocals`, `vocals+other`, `bass+vocals+other` (drums are never included in the synthetic mixes; the original column is the full file).
3. **Run chord detectors** on each mix (configurable).
4. **Write** `report.md`, `chords.full.json`, and `chords.first.json` under `out/<input-stem>/`.

## Requirements

- **Docker** with GPU support (`nvidia-container-toolkit` and `docker run --gpus all`) for the provided `run.sh` path.
- Audio placed under `audio/` when using `run.sh` (read-only mount).

Local Python runs are possible if you match the Dockerfile stack (PyTorch, Demucs, ffmpeg, ISMIR2019 clone at `/app/ismir2019` for the `ismir2019` detector).

## Quick start

```bash
mkdir -p audio out
cp /path/to/your/song.mp3 audio/
./run.sh song.mp3
```

Optional arguments are passed through to the pipeline, for example:

```bash
./run.sh song.mp3 --models chordino madmom ismir2019 --n 8
./run.sh song.mp3 --expected "C G Am F C G F C"
./run.sh song.mp3 --demucs-model htdemucs_ft --clean
```

Stems and mixes are kept by default so reruns can reuse cached WAVs. Pass `--clean` to remove `stems/` and `mixes/` after the run.

## CLI reference

| Argument | Description |
|----------|-------------|
| `input` | Audio file path (inside the container this is often `/audio/<file>`). |
| `--out` | Output directory (default in image: `/out`; `run.sh` mounts `./out`). |
| `--models` | One or more of: `chordino`, `madmom`, `ismir2019`. |
| `--n` | Number of opening **chord changes** to compare (default: 8). |
| `--expected` | Optional ground-truth sequence, e.g. `"C G Am F"`; sets comparison length and adds scoring in the report. |
| `--demucs-model` | Demucs pretrained name (default: `htdemucs_ft`). |
| `--clean` | Remove `stems/` and `mixes/` after completion. |

## Output layout

```
out/<Track Name>/
  report.md           # Markdown tables per model
  chords.full.json    # Full timelines per model × mix
  chords.first.json   # First N changes per model × mix
  stems/              # Cached Demucs WAVs (reused on reruns)
  mixes/              # Per-mix WAVs fed to detectors
```

## Build only

```bash
docker build -t chord-stem-lab:latest .
```

## License

Third-party components (Demucs, chord extractors, Madmom, ISMIR2019 chord recognition, PyTorch) keep their respective licenses. Add a project license file if you intend to distribute this repository.
# chord-stem-lab
# chord-stem-lab
# chord-stem-lab
# chord-stem-lab
# chord-stem-lab
# chord-stem-lab
# chord-stem-lab
# chord-stem-lab
# chord-stem-lab
