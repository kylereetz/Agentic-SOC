#!/bin/bash
# ===========================================================================
# RCA Patch Pilot — Remediation Script (Bash)
# ===========================================================================
# Patch ID   : RCA-20260316_191723-353
# Title      : Configure PAM TOTP (Google Authenticator)
# NIST Control: 3.5.3
# Finding    : Ubuntu system missing google-authenticator
# Generated  : 20260316_191723
# Status     : PENDING_APPROVAL — DO NOT EXECUTE WITHOUT HUMAN APPROVAL
# ===========================================================================
set -euo pipefail

echo "[RCA Patch Pilot] Starting remediation: Configure PAM TOTP (Google Authenticator)"
echo "[RCA Patch Pilot] NIST Control: 3.5.3"

# ---- FIX ----
apt-get update && apt-get install -y libpam-google-authenticator
systemctl restart ssh

# ---- VERIFICATION ----
grep 'pam_google_authenticator' /etc/pam.d/sshd

echo "[RCA Patch Pilot] Remediation complete. Please verify manually."
