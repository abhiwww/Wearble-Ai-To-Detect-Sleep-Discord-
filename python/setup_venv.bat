@echo off
echo Setting up Python virtual environment...
python -m venv venv
call venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
echo.
echo Setup complete! Virtual environment is ready.
pause
