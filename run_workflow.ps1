param (
    [Parameter(Mandatory=$true)]
    [string]$Audio, # Accepts a file, a comma-separated list, OR a folder directory path

    [Parameter(Mandatory=$true)]
    [string]$Script,

    [string]$OutputPrefix = "cloned_speech"
)

# Define paths
$VenvPython = "C:\Users\Naman\OneDrive\Desktop\Claude\xtts-env\Scripts\python.exe"
$Cwd = Get-Location
$TmpDir = Join-Path $Cwd "tmp"

# Generate a unique timestamp
$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$FinalOutput = "${OutputPrefix}_${Timestamp}.wav"

# Verify virtual environment python exists
if (-not (Test-Path $VenvPython)) {
    Write-Error "Virtual environment python not found at: $VenvPython"
    exit 1
}

# Ensure clean temporary directory
if (-not (Test-Path $TmpDir)) {
    New-Item -ItemType Directory -Path $TmpDir | Out-Null
}

# Resolve input: File, List, or Directory
$AudioFiles = @()

if (Test-Path $Audio -PathType Container) {
    # If the path is a folder, scan for all common audio files
    Write-Host "Detected directory input. Scanning for audio files..." -ForegroundColor Yellow
    #$SupportedExtensions = @('*.wav', '*.mp3', '*.m4a', '*.ogg', '*.flac')
        # Safe regex lookup covering all common formats case-insensitively
    $AudioFiles = Get-ChildItem -Path $Audio -File | Where-Object { 
        $_.Extension -match '^\.(wav|mp3|m4a|ogg|flac)$' 
    } | ForEach-Object { $_.FullName }

    
    if ($AudioFiles.Count -eq 0) {
        Write-Error "No supported audio files found inside the directory: $Audio"
        exit 1
    }
    Write-Host "Found $($AudioFiles.Count) audio files inside the folder." -ForegroundColor Green
} else {
    # Otherwise, treat it as a single file or a comma-separated string list
    $AudioFiles = $Audio -split "," | ForEach-Object { $_.Trim() }
}

$ProcessedAudioList = @()
$count = 1

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "Step 1/2: Optimizing all reference audio recordings..." -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan

foreach ($AudioFile in $AudioFiles) {
    if (-not (Test-Path $AudioFile)) {
        Write-Error "Reference track not found at: $AudioFile"
        exit 1
    }
    
    $OutFile = Join-Path $TmpDir "optimized_input_${count}.wav"
    Write-Host "Normalizing Recording $count/$($AudioFiles.Count): $AudioFile" -ForegroundColor Magenta
    
    & $VenvPython prep_audio.py $AudioFile $OutFile
    
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Audio normalization failed for $AudioFile. Exiting workflow."
        exit 1
    }
    
    $ProcessedAudioList += $OutFile
    $count++
}

Write-Host ""
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "Step 2/2: Auto-slicing and cloning voice via XTTS v2..." -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan

# Concatenate multiple paths with a delimiter (|) for python sys.argv processing
$PassedAudioArgs = $ProcessedAudioList -join "|"

& $VenvPython run_clone.py $PassedAudioArgs $Script $FinalOutput

if ($LASTEXITCODE -ne 0) {
    Write-Error "Voice cloning failed. Exiting workflow."
    exit 1
}

Write-Host ""
Write-Host "Workflow completed successfully! Final output saved to: $FinalOutput" -ForegroundColor Green
