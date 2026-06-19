#!/bin/sh
set -e

SENTINEL="/data/.downloaded"

if [ -f "$SENTINEL" ]; then
  echo "Dataset already present, skipping download and preprocessing."
  exit 0
fi

echo "Downloading viz-stimulus dataset..."
curl -fL "https://zenodo.org/records/10519411/files/viz-stimulus.zip?download=1" -o /tmp/viz-stimulus.zip

echo "Unpacking..."
unzip /tmp/viz-stimulus.zip -d /tmp/viz-stimulus
rm /tmp/viz-stimulus.zip

echo "Unpacking monitors..."
unzip /tmp/viz-stimulus/viz-stimulus/monitors.zip -d /data/monitors

echo "Copying network and position files..."
cp /tmp/viz-stimulus/viz-stimulus/network/* /data/
cp /tmp/viz-stimulus/viz-stimulus/positions/* /data/
rm -rf /tmp/viz-stimulus

echo "Preprocessing..."
uv run --group preprocess python /app/preprocess.py \
  --monitors-dir /data/monitors \
  --output-dir /data

echo "Cleaning up monitors..."
rm -rf /data/monitors

touch "$SENTINEL"
echo "Done."
