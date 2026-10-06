#!/bin/bash
set -e

echo "=== Setting up Montreal Forced Aligner ==="

conda install -c conda-forge montreal-forced-aligner -y 2>/dev/null || \
    pip install montreal-forced-aligner

echo "[1/3] Downloading Hindi acoustic model..."
mfa model download acoustic hindi_mfa || echo "Hindi MFA model: check manually at mfa-models.readthedocs.io"

echo "[2/3] Downloading Hindi dictionary..."
mfa model download dictionary hindi_mfa || echo "Hindi dictionary: check manually"

echo "[3/3] Checking Telugu (may not exist — will use Hindi fallback)..."
mfa model download acoustic telugu_mfa 2>/dev/null || \
    echo "Telugu MFA model not available — using Hindi acoustic model as fallback for Telugu alignment"

echo ""
echo "=== MFA setup complete ==="
echo "Available models:"
mfa model list acoustic 2>/dev/null || true
