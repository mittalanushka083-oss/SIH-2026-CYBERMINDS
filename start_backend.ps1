Set-Location "$PSScriptRoot"
if (!(Test-Path "backend\.venv")) {
  python -m venv backend\.venv
}
& "backend\.venv\Scripts\Activate.ps1"
pip install -r backend\requirements.txt
$env:PYTHONPATH="."
python -m uvicorn backend.app.main:app --reload --port 8000
