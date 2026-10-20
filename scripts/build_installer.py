"""
Remodax - Windows Installer Builder
Compiles the onedir PyInstaller build into an Inno Setup installer:
dist/Installer/Remodax_Setup.exe
"""

import sys
import shutil
import subprocess
from pathlib import Path


def find_iscc() -> Path:
    """Finds the Inno Setup command-line compiler (ISCC.exe) across common Windows locations."""
    # 1. System PATH
    which_iscc = shutil.which("iscc") or shutil.which("ISCC")
    if which_iscc:
        return Path(which_iscc)

    # 2. Known standard installation paths
    candidate_paths = [
        Path(r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe"),
        Path(r"C:\Program Files\Inno Setup 6\ISCC.exe"),
        Path(r"C:\Users\User\AppData\Local\Programs\Inno Setup 6\ISCC.exe"),
        Path(r"C:\Users\User\AppData\Local\Programs\Antigravity IDE\resources\app\node_modules\innosetup\bin\ISCC.exe"),
    ]

    for p in candidate_paths:
        if p.exists():
            return p

    raise FileNotFoundError(
        "No se encontró el compilador de Inno Setup (ISCC.exe). "
        "Asegúrate de tener Inno Setup 6 instalado."
    )


def build_installer() -> int:
    root_dir = Path(__file__).resolve().parent.parent
    dist_dir = root_dir / "dist"
    app_dir = dist_dir / "Remodax"
    exe_file = app_dir / "Remodax.exe"
    installer_dir = dist_dir / "Installer"
    iss_file = root_dir / "scripts" / "remodax_installer.iss"

    print("==================================================")
    print("  Remodax - Generador de Instalador Inno Setup")
    print("==================================================")
    print(f"Directorio raíz: {root_dir}")

    # 1. Verificar binario base
    if not exe_file.exists():
        print(f"[INFO] No se encontró {exe_file}. Compilando con PyInstaller primero...")
        build_exe_script = root_dir / "scripts" / "build_exe.py"
        res = subprocess.run([sys.executable, str(build_exe_script)])
        if res.returncode != 0:
            print(f"[ERROR] Error al generar el ejecutable base: {res.returncode}")
            return res.returncode

    # 2. Auditoría de Seguridad Previa al Empaquetado
    print("\n[INFO] Ejecutando auditoría de seguridad previa al empaquetado...")
    forbidden_extensions = {".env", ".db", ".sqlite", ".sqlite3", ".key"}
    forbidden_names = {"credentials.json", "secrets.json", "api_keys.json", ".env"}
    found_sensitive = []
    for f in app_dir.rglob("*"):
        if f.is_file():
            lower_name = f.name.lower()
            if f.suffix.lower() in forbidden_extensions and "cacert" not in lower_name:
                found_sensitive.append(f)
            elif any(fn in lower_name for fn in forbidden_names):
                found_sensitive.append(f)

    if found_sensitive:
        print("[ERROR CRÍTICO] Se detectaron archivos sensibles en el directorio de empaquetado:")
        for sf in found_sensitive:
            print(f"  - {sf}")
        print("Abortando generación del instalador para proteger la privacidad.")
        return 1

    print("[OK] Auditoría de seguridad superada: Ningún archivo sensible detectado.")

    # 3. Localizar compilador Inno Setup
    try:
        iscc_path = find_iscc()
        print(f"[INFO] Compilador Inno Setup localizado en: {iscc_path}")
    except FileNotFoundError as err:
        print(f"[ERROR] {err}")
        return 1

    # 4. Crear carpeta de destino
    installer_dir.mkdir(parents=True, exist_ok=True)

    # 5. Compilar instalador
    print(f"\n[INFO] Compilando script Inno Setup: {iss_file}...")
    cmd = [str(iscc_path), str(iss_file)]
    res = subprocess.run(cmd)

    if res.returncode != 0:
        print(f"\n[ERROR] Inno Setup finalizó con código de error: {res.returncode}")
        return res.returncode

    final_setup = installer_dir / "Remodax_Setup.exe"
    if final_setup.exists():
        size_mb = final_setup.stat().st_size / (1024 * 1024)
        print("==================================================")
        print("  INSTALADOR GENERADO EXITOSAMENTE")
        print("==================================================")
        print(f"Instalador:     {final_setup}")
        print(f"Tamaño binario: {size_mb:.2f} MB")
        print("==================================================")
        return 0
    else:
        print(f"[ERROR] No se encontró el instalador generado en {final_setup}")
        return 1


if __name__ == "__main__":
    sys.exit(build_installer())
