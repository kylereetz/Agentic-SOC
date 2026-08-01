"""
RCA Audio Utility: OS-level sound notifications for SOC milestones.
Uses PowerShell to play .wav files from the user's music directory.
"""

import os
import subprocess
import logging
import random

logger = logging.getLogger(__name__)

# Project Root & Sounds Directory
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
SOUNDS_DIR = os.getenv("SOUNDS_DIR", os.path.join(_PROJECT_ROOT, "Model Complete Sounds"))

def play_sound(sound_name: str, sync: bool = False):
    """
    Play a specific .wav file from the sounds directory.
    If sound_name is 'random', picks a random file.
    """
    if not os.path.exists(SOUNDS_DIR):
        # Gracefully handle missing sound directory without breaking SOC execution
        logger.warning(f"Sound directory not found: {SOUNDS_DIR}")
        return

    target_file = None
    if sound_name == "random":
        files = [f for f in os.listdir(SOUNDS_DIR) if f.endswith(".wav")]
        if files:
            target_file = os.path.join(SOUNDS_DIR, random.choice(files))
    else:
        # Ensure .wav extension
        if not sound_name.endswith(".wav"):
            sound_name += ".wav"
        
        potential_path = os.path.join(SOUNDS_DIR, sound_name)
        if os.path.exists(potential_path):
            target_file = potential_path
        else:
            # Try case-insensitive search
            files = os.listdir(SOUNDS_DIR)
            for f in files:
                if f.lower() == sound_name.lower():
                    target_file = os.path.join(SOUNDS_DIR, f)
                    break

    if not target_file:
        logger.warning(f"Sound file not found: {sound_name}")
        return

    # Use PowerShell to play the sound
    # Using [System.Media.SoundPlayer] for .wav files
    method = "PlaySync()" if sync else "Play()"
    ps_command = f"(New-Object System.Media.SoundPlayer '{target_file}').{method}"
    
    try:
        # Run in background to avoid blocking agent execution
        subprocess.Popen(["powershell", "-Command", ps_command], 
                         stdout=subprocess.DEVNULL, 
                         stderr=subprocess.DEVNULL)
        logger.info(f"Triggered audio notification: {os.path.basename(target_file)}")
    except Exception as e:
        logger.error(f"Failed to play sound {sound_name}: {e}")

def play_milestone_learning():
    """Triggered when a MARL Q-Value milestone is reached."""
    play_sound("Orge MAgi - We're not Brainless anymore.wav")

def play_critical_alert():
    """Triggered when a CRITICAL alert is detected by Triage."""
    play_sound("Human - The Town is under Attack.wav")

def play_action_completed():
    """Triggered when a containment action is successfully applied."""
    play_sound("Peon - Work Complete.wav")
