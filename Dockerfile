FROM pytorch/pytorch:2.3.0-cuda12.1-cudnn8-runtime

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    TORCH_HOME=/root/.cache/torch

RUN apt-get update && apt-get install -y --no-install-recommends \
      ffmpeg sox libsndfile1 git ca-certificates build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# madmom: needs cython at build time and numpy<1.24 (np.int usage) — both satisfied above.
# Python 3.10 moved abstract base classes to collections.abc; patch madmom's imports.
RUN pip install --no-cache-dir "cython<3" && pip install --no-cache-dir madmom==0.16.1 \
 && MADMOM_DIR=/opt/conda/lib/python3.10/site-packages/madmom \
 && grep -rl "from collections import" "$MADMOM_DIR" \
      | xargs sed -i -E 's/from collections import (MutableSequence|Iterable|Mapping|MutableMapping|Callable|Sequence|Set)/from collections.abc import \1/g'

# ISMIR2019 Large-Vocabulary Chord Recognition (pretrained checkpoints bundled in repo).
RUN git clone --depth 1 https://github.com/music-x-lab/ISMIR2019-Large-Vocabulary-Chord-Recognition.git /app/ismir2019

# Pre-cache Demucs weights at build time so first run is fast.
RUN python -c "from demucs.pretrained import get_model; get_model('htdemucs_ft')"

COPY pipeline.py .

ENTRYPOINT ["python", "pipeline.py"]
