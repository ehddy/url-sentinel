@echo off

cd /d %~dp0

python -m venv venv

call venv\Scripts\activate

python -m pip install --upgrade pip

pip install -r requirements.txt

python -m playwright install

pip install --upgrade crawl4ai rich

echo.
echo =========================
echo Setup Complete
echo =========================

pause