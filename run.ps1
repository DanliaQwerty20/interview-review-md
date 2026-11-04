$ErrorActionPreference = 'Stop'

if (-not (Test-Path -LiteralPath '.venv')) {
    py -m venv .venv
}

& .\.venv\Scripts\python.exe -m pip install --upgrade pip
& .\.venv\Scripts\python.exe -m pip install -e .
& .\.venv\Scripts\python.exe -m streamlit run app.py

