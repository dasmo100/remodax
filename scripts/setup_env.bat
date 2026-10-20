@echo off
REM ==============================================================================
REM Remodax - Setup Virtual Environment & Dependencies for Windows 10/11
REM ==============================================================================

echo [Remodax] Configurando entorno de desarrollo...

IF NOT EXIST "venv" (
    echo Creando entorno virtual 'venv'...
    python -m venv venv
) ELSE (
    echo El entorno virtual 'venv' ya existe.
)

echo Activando entorno virtual...
call venv\Scripts\activate.bat

echo Actualizando pip...
python -m pip install --upgrade pip

echo Instalando dependencias desde requirements.txt...
pip install -r requirements.txt

echo.
echo ==============================================================================
echo [LISTO] Entorno configurado exitosamente.
echo Para iniciar la aplicacion ejecuta:
echo     venv\Scripts\activate
echo     python main.py
echo ==============================================================================
