$ErrorActionPreference = "Stop"

Set-Location -Path $PSScriptRoot

.\.venv\Scripts\python.exe main.py

Read-Host "Press Enter to exit"