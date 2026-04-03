#!/bin/bash
# ===========================================================================
# RCA Patch Pilot — ROLLBACK Script (Bash)
# ===========================================================================
# Patch ID   : RCA-20260316_191723-353
# Title      : ROLLBACK — Configure PAM TOTP (Google Authenticator)
# ===========================================================================
set -euo pipefail

echo "[RCA Patch Pilot] Rolling back: Configure PAM TOTP (Google Authenticator)"

sed -i '/pam_google_authenticator/d' /etc/pam.d/sshd

echo "[RCA Patch Pilot] Rollback complete."
