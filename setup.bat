@echo off
echo Setting up Trading System...
python -m venv venv
call venv\Scripts\activate
pip install -r requirements.txt
if not exist .env (
    copy .env.example .env
    echo.
    echo *** Edit .env and add your API keys ***
    echo    ANTHROPIC_API_KEY  - get at console.anthropic.com
    echo    COINBASE_API_KEY   - get at coinbase.com/settings/api
    echo.
)
echo.
echo Setup complete! Run: start.bat
pause
