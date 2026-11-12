#!/usr/bin/env bash
# Creates a self-signed certificate for https://localhost (development and demo only).
set -euo pipefail
mkdir -p certs
# MSYS_NO_PATHCONV stops Git Bash from rewriting "/CN=localhost" into a Windows path.
MSYS_NO_PATHCONV=1 openssl req -x509 -newkey rsa:2048 -nodes -days 365 \
  -keyout certs/dev-key.pem -out certs/dev-cert.pem \
  -subj "/CN=localhost" -addext "subjectAltName=DNS:localhost,IP:127.0.0.1"
echo "Created certs/dev-cert.pem and certs/dev-key.pem (certs/ is git-ignored; never commit the key)."
