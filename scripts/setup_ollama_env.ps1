# --- Agentic SOC High-Performance VRAM Optimization ---
# 
# This script sets the environment variables required for the 'Multi-Head' model 
# design on a 16GB RTX 4080. It prevents the 'Ollama model thumping' issue 
# and ensures parallel agent performance.

Write-Output "--- Configuring Ollama for Agentic SOC (16GB VRAM Optimized) ---"

# 1. Total VRAM Commitment (16GB)
[Environment]::SetEnvironmentVariable("OLLAMA_MAX_VRAM", "16000000000", "User")
Write-Output "SET: OLLAMA_MAX_VRAM = 16GB"

# 2. Parallel Processing (4 heads max)
[Environment]::SetEnvironmentVariable("OLLAMA_NUM_PARALLEL", "4", "User")
Write-Output "SET: OLLAMA_NUM_PARALLEL = 4"

# 3. Model Persistence (Keep models in VRAM indefinitely)
[Environment]::SetEnvironmentVariable("OLLAMA_KEEP_ALIVE", "-1", "User")
Write-Output "SET: OLLAMA_KEEP_ALIVE = -1 (Persistent in VRAM)"

Write-Output "--------------------------------------------------------"
Write-Output "SUCCESS: High-performance environment variables set for User."
Write-Output "IMPORTANT: You must RESTART YOUR TERMINAL (and Ollama Desktop) for these changes to take effect."
Write-Output "--------------------------------------------------------"
