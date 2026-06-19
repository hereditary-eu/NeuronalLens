#!/bin/sh
set -e

SENTINEL="/data/.downloaded"

if [ -f "$SENTINEL" ]; then
  echo "Dataset already present, skipping download and preprocessing."
  exit 0
fi

echo "Downloading viz-stimulus dataset..."
curl -fL --progress-bar "https://zenodo.org/records/10519411/files/viz-stimulus.zip?download=1" -o /tmp/viz-stimulus.zip
unzip /tmp/viz-stimulus.zip -d /data
rm /tmp/viz-stimulus.zip

echo "Preprocessing..."
uv run --group preprocess python /app/preprocess.py \
  --monitors-dir /data/monitors \
  --output-dir /data

touch "$SENTINEL"
echo "Done."
