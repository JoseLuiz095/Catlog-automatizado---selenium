@echo off
setlocal

REM ============================
REM Configurações (edite se necessário)
REM ============================
set PYFILE=script.py
set VENV_DIR=.venv
REM ============================

echo.
echo ==== AutoStarter para SyncThru FTP =====
echo Pasta atual: %cd%
echo Script Python: %PYFILE%
echo Venv: %VENV_DIR%
echo.

REM 1) Detecta python (py preferido)
where py >nul 2>&1
if %errorlevel%==0 (
    set PYEXEC=py
) else (
    where python >nul 2>&1
    if %errorlevel%==0 (
        set PYEXEC=python
    ) else (
        echo ERRO: Python nao encontrado no PATH.
        echo Instale o Python e marque "Add to PATH" durante a instalacao.
        pause
        exit /b 1
    )
)

echo Usando Python: %PYEXEC%

REM 2) Cria venv se nao existir
if not exist "%VENV_DIR%\Scripts\activate" (
    echo Criando virtualenv em %VENV_DIR%...
    %PYEXEC% -m venv %VENV_DIR%
    if errorlevel 1 (
        echo Falha ao criar venv.
        pause
        exit /b 1
    )
) else (
    echo Virtualenv ja existe.
)

REM 3) Ativa venv
call "%VENV_DIR%\Scripts\activate.bat"
if errorlevel 1 (
    echo Falha ao ativar venv.
    pause
    exit /b 1
)

REM 4) Instala dependencias (se necessario)
echo Instalando dependencias (selenium, webdriver-manager)...
pip install --upgrade pip >nul
pip show selenium >nul 2>&1
if errorlevel 1 (
    pip install selenium
)
pip show webdriver-manager >nul 2>&1
if errorlevel 1 (
    pip install webdriver-manager
)

echo Dependencias OK.
echo.

REM 5) Executa o script
if not exist "%PYFILE%" (
    echo Arquivo %PYFILE% nao encontrado na pasta atual.
    pause
    exit /b 1
)

echo Iniciando o script... (pressione Ctrl+C para cancelar)
%PYEXEC% "%PYFILE%"

REM 6) Final
echo.
echo Script finalizado.
pause

endlocal
