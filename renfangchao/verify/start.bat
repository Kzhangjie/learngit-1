@echo off
call conda activate d:\projects\llm_qa\pe
cd d:\projects\\llm_qa
start /b cmd /c streamlit run  renfangchao\verify\streamlit_app.py --server.port 8502