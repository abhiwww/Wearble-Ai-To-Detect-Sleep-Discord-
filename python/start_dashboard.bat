@echo off
title Sleep Monitor - Streamlit Dashboard
call venv\Scripts\activate
echo Starting Streamlit dashboard...
streamlit run dashboard.py
pause
