function antigravity-cli {
    param([Parameter(ValueFromPipeline = $true)]$InputObject, [string]$instruction)
    Write-Host "[Antigravity] Processing instruction: $instruction" -ForegroundColor Blue
}

$MaxLoops = 100
$CurrentLoop = 1
$TargetFiles = @("soc\api\main.py", "soc\tests\test_main.py")

# Initialize scratchpad
Set-Content -Path "SCRATCHPAD.md" -Value "Starting new task..."

while ($CurrentLoop -le $MaxLoops) {
    Write-Host "--- Iteration $CurrentLoop ---" -ForegroundColor Cyan
    
    # 1. Provide Context to Antigravity
    # NOTE: Using internal function mock
    Get-Content "SYSTEM.md", "TASK.md", "SCRATCHPAD.md", "soc\api\main.py", "soc\tests\test_main.py" | antigravity-cli --instruction "Read the task, update the target files, and append your progress to SCRATCHPAD.md before exiting."
    
    # 2. Objective Verification
    Write-Host "Running tests..."
    # Execute pytest and capture output. In PowerShell, we check $LASTEXITCODE for pass/fail.
    # Execute pytest using the venv and capture output.
    .\.venv\Scripts\python -m pytest soc\tests\test_main.py 2>&1 | Out-File -FilePath "test_output.txt"
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Tests passed. Task complete." -ForegroundColor Green
        exit 0
    }
    else {
        Write-Host "Tests failed. Appending errors to scratchpad for the next iteration..." -ForegroundColor Yellow
        Add-Content -Path "SCRATCHPAD.md" -Value "`n### Test Failure (Loop $CurrentLoop)"
        Get-Content "test_output.txt" | Add-Content -Path "SCRATCHPAD.md"
    }
    
    $CurrentLoop++
}

Write-Host "Max loops reached without passing tests. Intervention required." -ForegroundColor Red