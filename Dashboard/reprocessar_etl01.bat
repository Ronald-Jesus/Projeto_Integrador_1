@echo off
title Reprocessando ETL 01...
set KAGGLE_API_TOKEN=KGAT_8afdffa9194200cbcdf33dd2875c9a02
cd /d "%~dp0src\scripts"
python etl_01_kaggle_fitlife.py
echo.
echo Regenerando banco de dados...
python gerar_banco_dados.py
echo.
echo Copiando banco para pasta raiz...
python -c "import shutil, os; src=os.path.join('..','..','data','processed','saude_mental.db'); dest=os.path.join('..','..','saude_mental.db'); shutil.copy2(src,dest) if os.path.exists(src) else print('banco nao encontrado em',src)"
echo.
echo Pronto! Recarregue o dashboard (F5 no navegador).
pause
