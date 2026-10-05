param (
    [Parameter(Mandatory=$true)]
    [string]$Audio,

    [Parameter(Mandatory=$true)]
    [string]$Script,

    [string]$Output = "output.wav"
)

# Define the absolute path to your virtual environment
$VenvPython = "C:\Users\Naman\OneDrive\Desktop\Claude\xtts-env\Scripts\python.exe"

# Check if the virtual environment python exists
if (-not (Test-Path $VenvPython)) {
    Write-Error "Virtual environment python not found at: $VenvPython"
    exit 1
}

Write-Host "Activating venv and running TTS generation..." -ForegroundColor Cyan

# Run your Python script using the venv's python executable, passing arguments through
& $VenvPython run_clone.py $Audio $Script $Output