"""Chord detection A/B lab: runs chord detection on the original mix and on
several stem combinations produced by Demucs, then writes a markdown report
comparing the first N chord changes per mix per model."""

import argparse
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import torch
from demucs.apply import apply_model
from demucs.audio import AudioFile, save_audio
from demucs.pretrained import get_model

# mix name -> stems to sum. None = use original input file.
MIXES = {
    "original":            None,
    "bass+other":          ["bass", "other"],
    "bass+vocals":         ["bass", "vocals"],
    "vocals+other":        ["vocals", "other"],
    "bass+vocals+other":   ["bass", "vocals", "other"],
}

STEM_NAMES = ("drums", "bass", "other", "vocals")


def separate_stems(input_path: Path, run_dir: Path, model_name: str) -> dict[str, Path]:
    stems_dir = run_dir / "stems"
    cached = {s: stems_dir / f"{s}.wav" for s in STEM_NAMES}
    if all(p.exists() for p in cached.values()):
        print(f"[demucs] reusing cached stems in {stems_dir}", flush=True)
        return cached

    print(f"[demucs] loading {model_name}", flush=True)
    model = get_model(model_name)
    model.eval()
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"[demucs] device={device}", flush=True)
    model.to(device)

    wav = AudioFile(str(input_path)).read(
        streams=0, samplerate=model.samplerate, channels=model.audio_channels
    )
    ref = wav.mean(0)
    wav_norm = (wav - ref.mean()) / ref.std()
    sources = apply_model(model, wav_norm[None], device=device, progress=True)[0]
    sources = sources * ref.std() + ref.mean()

    stems_dir.mkdir(parents=True, exist_ok=True)
    out = {}
    for source, name in zip(sources, model.sources):
        p = stems_dir / f"{name}.wav"
        save_audio(source, str(p), samplerate=model.samplerate)
        out[name] = p
        print(f"[demucs] {name} -> {p.name}", flush=True)
    return out


def ffmpeg_mix(inputs: list[Path], out_path: Path) -> None:
    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error"]
    for p in inputs:
        cmd += ["-i", str(p)]
    n = len(inputs)
    cmd += [
        "-filter_complex", f"amix=inputs={n},volume={n}",
        "-c:a", "pcm_s16le",
        str(out_path),
    ]
    subprocess.run(cmd, check=True)


def ffmpeg_to_wav(input_path: Path, out_path: Path) -> None:
    subprocess.run(
        ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
         "-i", str(input_path), "-c:a", "pcm_s16le", str(out_path)],
        check=True,
    )


def detect_chordino(audio_path: Path) -> list[dict]:
    from chord_extractor.extractors import Chordino
    chordino = Chordino()
    return [
        {"time": float(c.timestamp), "chord": c.chord}
        for c in chordino.extract(str(audio_path))
    ]


def detect_madmom(audio_path: Path) -> list[dict]:
    from madmom.audio.chroma import DeepChromaProcessor
    from madmom.features.chords import DeepChromaChordRecognitionProcessor
    chroma = DeepChromaProcessor()(str(audio_path))
    return [
        {"time": float(start), "chord": label}
        for start, _end, label in DeepChromaChordRecognitionProcessor()(chroma)
    ]


ISMIR_DIR = Path("/app/ismir2019")


def detect_ismir2019(audio_path: Path, chord_dict: str = "submission") -> list[dict]:
    import tempfile
    lab_path = Path(tempfile.mkstemp(suffix=".lab")[1])
    try:
        subprocess.run(
            ["python", "chord_recognition.py", str(audio_path), str(lab_path), chord_dict],
            check=True, cwd=str(ISMIR_DIR),
        )
        chords = []
        for line in lab_path.read_text().splitlines():
            parts = line.strip().split()
            if len(parts) >= 3:
                chords.append({"time": float(parts[0]), "chord": " ".join(parts[2:])})
        return chords
    finally:
        lab_path.unlink(missing_ok=True)


DETECTORS = {
    "chordino": detect_chordino,
    "madmom": detect_madmom,
    "ismir2019": detect_ismir2019,
}


def normalize_chord(label: str) -> str:
    """Rewrite Harte-style and mixed labels to a compact form: A:maj→A, A:min→Am, A:min7→Am7, etc."""
    if not label or label in ("N", "X", "None"):
        return "N"
    label = label.strip().replace("♯", "#").replace("♭", "b")
    if "/" in label:
        label = label.split("/", 1)[0]
    if ":" in label:
        root, quality = label.split(":", 1)
        if quality == "maj":
            label = root
        elif quality == "min":
            label = root + "m"
        elif quality.startswith("min"):
            label = root + "m" + quality[3:]
        else:
            label = root + quality
    if label and label[0].isalpha():
        label = label[0].upper() + label[1:]
    return label


def chord_root(label: str) -> str:
    if not label or label == "N":
        return label
    if len(label) >= 2 and label[1] in ("#", "b"):
        return label[:2]
    return label[:1]


def first_n_changes(chords: list[dict], n: int) -> list[dict]:
    out, last = [], None
    for c in chords:
        label = normalize_chord(c["chord"])
        if label == "N":
            continue
        if label != last:
            out.append({"time": c["time"], "chord": label})
            last = label
            if len(out) >= n:
                break
    return out


def parse_expected(s: str) -> list[str]:
    tokens = [t for t in re.split(r"[,\s]+", s.strip()) if t]
    return [normalize_chord(t) for t in tokens]


def score_sequence(detected: list[dict], expected: list[str]) -> tuple[int, int]:
    exact = root = 0
    for i, exp in enumerate(expected):
        if i >= len(detected):
            break
        got = detected[i]["chord"]
        if got == exp:
            exact += 1
        if chord_root(got) == chord_root(exp):
            root += 1
    return exact, root


def write_report(
    first_chords: dict,
    n: int,
    report_path: Path,
    input_name: str,
    expected: list[str] | None,
) -> None:
    lines = [
        f"# Chord detection A/B — `{input_name}`",
        "",
        f"_Generated {datetime.now().isoformat(timespec='seconds')} — first {n} chord changes per mix._",
        "",
    ]
    if expected:
        lines.append(
            f"**Expected sequence** ({len(expected)}): " + " ".join(f"`{e}`" for e in expected)
        )
        lines.append("")

    for model_name, per_mix in first_chords.items():
        lines.append(f"## Model: `{model_name}`")
        lines.append("")
        mixes = list(per_mix.keys())
        headers = ["#"]
        if expected:
            headers.append("expected")
        headers += mixes
        lines.append("| " + " | ".join(headers) + " |")
        lines.append("|" + "|".join(["---"] * len(headers)) + "|")
        for i in range(n):
            row = [str(i + 1)]
            if expected:
                row.append(f"`{expected[i]}`" if i < len(expected) else "—")
            for m in mixes:
                chords = per_mix[m]
                row.append(f"`{chords[i]['chord']}`" if i < len(chords) else "—")
            lines.append("| " + " | ".join(row) + " |")
        lines.append("")

        if expected:
            scores = {m: score_sequence(per_mix[m], expected) for m in mixes}
            best_exact = max(s[0] for s in scores.values())
            lines.append("**Match vs expected (exact / same-root):**")
            lines.append("")
            for m, (ex, rt) in scores.items():
                marker = "  ← best" if ex == best_exact else ""
                lines.append(f"- `{m}`: {ex}/{len(expected)} exact, {rt}/{len(expected)} same-root{marker}")
            lines.append("")

    report_path.write_text("\n".join(lines))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="Audio file (mp3/wav/flac/…)")
    parser.add_argument("--out", type=Path, default=Path("/out"))
    parser.add_argument("--models", nargs="+", default=["chordino"],
                        choices=list(DETECTORS))
    parser.add_argument("--n", type=int, default=8,
                        help="How many opening chord changes to compare (default: 8; overridden by --expected length)")
    parser.add_argument("--expected", type=str, default="",
                        help='Expected opening sequence, e.g. "C G Am F C G F C"')
    parser.add_argument("--demucs-model", default="htdemucs_ft")
    parser.add_argument("--clean", action="store_true",
                        help="Delete stems/mixes after run (default: keep for reuse)")
    args = parser.parse_args()

    input_path = args.input.resolve()
    if not input_path.exists():
        sys.exit(f"input not found: {input_path}")

    expected = parse_expected(args.expected) if args.expected else None
    n = len(expected) if expected else args.n

    run_dir = args.out / input_path.stem
    run_dir.mkdir(parents=True, exist_ok=True)
    mix_dir = run_dir / "mixes"
    mix_dir.mkdir(exist_ok=True)

    stems = separate_stems(input_path, run_dir, args.demucs_model)

    mix_paths: dict[str, Path] = {}
    for mix_name, stem_names in MIXES.items():
        out_wav = mix_dir / f"{mix_name}.wav"
        if not out_wav.exists():
            if stem_names is None:
                ffmpeg_to_wav(input_path, out_wav)
            else:
                ffmpeg_mix([stems[s] for s in stem_names], out_wav)
        mix_paths[mix_name] = out_wav
        print(f"[mix] {mix_name}", flush=True)

    all_chords: dict[str, dict[str, list[dict]]] = {}
    first_chords: dict[str, dict[str, list[dict]]] = {}
    for model_name in args.models:
        detect = DETECTORS[model_name]
        all_chords[model_name] = {}
        first_chords[model_name] = {}
        for mix_name, mix_path in mix_paths.items():
            print(f"[{model_name}] detecting on {mix_name}", flush=True)
            chords = detect(mix_path)
            all_chords[model_name][mix_name] = chords
            first_chords[model_name][mix_name] = first_n_changes(chords, n)

    (run_dir / "chords.full.json").write_text(json.dumps(all_chords, indent=2))
    (run_dir / "chords.first.json").write_text(json.dumps(first_chords, indent=2))
    report_path = run_dir / "report.md"
    write_report(first_chords, n, report_path, input_path.name, expected)

    if args.clean:
        shutil.rmtree(run_dir / "stems", ignore_errors=True)
        shutil.rmtree(mix_dir, ignore_errors=True)

    print(f"\nDone. Report: {report_path}\n")
    print(report_path.read_text())


if __name__ == "__main__":
    main()
