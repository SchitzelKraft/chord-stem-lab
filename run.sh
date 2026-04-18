#!/usr/bin/env bash
set -euo pipefail

# Usage: ./run.sh audio/song.mp3 [--models chordino autochord] [--n 8] [--keep-stems]

HERE="$(cd "$(dirname "$0")" && pwd)"
IMAGE="chord-stem-lab:latest"

if ! docker image inspect "$IMAGE" >/dev/null 2>&1; then
  echo "[run] building image $IMAGE ..."
  docker build -t "$IMAGE" "$HERE"
fi

if [ $# -lt 1 ]; then
  echo "usage: $0 <audio-file-inside-audio/> [pipeline args...]" >&2
  exit 2
fi

INPUT_REL="$1"; shift
INPUT_BASENAME="$(basename "$INPUT_REL")"

docker run --rm --gpus all \
  -v "$HERE/audio:/audio:ro" \
  -v "$HERE/out:/out" \
  "$IMAGE" \
  "/audio/$INPUT_BASENAME" --out /out "$@"
