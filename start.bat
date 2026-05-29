@echo off
call venv\Scripts\activate
streamlit run app.py --server.port 8501 --browser.gatherUsageStats false
