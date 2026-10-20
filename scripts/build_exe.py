"""
Remodax - PyInstaller Executable Builder
Builds a standalone, optimized Windows 10/11 .exe binary in onedir mode
with all required assets, icons, dynamic audio backends, and AI dependencies.
"""

import sys
import shutil
import struct
import subprocess
from pathlib import Path


def ensure_app_icon(icons_dir: Path) -> Path:
    """Ensures a multi-resolution Windows .ico file exists for PyInstaller."""
    ico_path = icons_dir / "app_icon.ico"
    png_path = icons_dir / "logoDany.png"

    if ico_path.exists() and ico_path.stat().st_size > 1000:
        return ico_path

    if not png_path.exists():
        return ico_path

    print("[INFO] Generando icono multirresolución app_icon.ico desde logoDany.png...")
    try:
        from PySide6.QtGui import QImage, QPainter
        from PySide6.QtCore import QBuffer, QIODevice, Qt

        sizes = [16, 24, 32, 48, 64, 128, 256]
        src_img = QImage(str(png_path))

        png_datas = []
        for s in sizes:
            scaled = src_img.scaled(
                s, s,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            canvas = QImage(s, s, QImage.Format.Format_ARGB32)
            canvas.fill(0)
            p = QPainter(canvas)
            x = (s - scaled.width()) // 2
            y = (s - scaled.height()) // 2
            p.drawImage(x, y, scaled)
            p.end()

            buf = QBuffer()
            buf.open(QIODevice.OpenModeFlag.WriteOnly)
            canvas.save(buf, "PNG")
            png_datas.append((s, bytes(buf.data())))

        header = struct.pack("<HHH", 0, 1, len(png_datas))
        offset = 6 + 16 * len(png_datas)
        entries = []
        for s, data in png_datas:
            w = 0 if s >= 256 else s
            h = 0 if s >= 256 else s
            entry = struct.pack("<BBBBHHII", w, h, 0, 0, 1, 32, len(data), offset)
            entries.append(entry)
            offset += len(data)

        with open(ico_path, "wb") as f:
            f.write(header)
            for e in entries:
                f.write(e)
            for _, data in png_datas:
                f.write(data)

        print("[OK] app_icon.ico generado exitosamente con 7 resoluciones.")
    except Exception as ex:
        print(f"[AVISO] No se pudo generar app_icon.ico automáticamente: {ex}")

    return ico_path


def build() -> int:
    root_dir = Path(__file__).resolve().parent.parent
    main_script = root_dir / "main.py"
    assets_dir = root_dir / "assets"
    icons_dir = assets_dir / "icons"
    dist_dir = root_dir / "dist"
    build_dir = root_dir / "build"

    print("==================================================")
    print("  Remodax - Generador de Ejecutable Windows 10/11")
    print("==================================================")
    print(f"Directorio raíz: {root_dir}")
    print(f"Python en uso:   {sys.executable} ({sys.version.split()[0]})")

    # 1. Asegurar icono
    ico_path = ensure_app_icon(icons_dir)

    # 2. PyInstaller arguments
    cmd = [
        sys.executable,
        "-m", "PyInstaller",
        "--name=Remodax",
        "--noconsole",          # Oculta la consola de depuración en modo escritorio
        "--onedir",             # Modo directorio portable para máxima compatibilidad con PySide6 y QtWebEngine
        "--clean",
        "--noconfirm",          # Sobreescribe salida anterior sin pedir confirmación manual
        f"--distpath={dist_dir}",
        f"--workpath={build_dir}",
        f"--add-data={assets_dir};assets",
    ]

    # Icono del ejecutable
    if ico_path.exists():
        cmd.append(f"--icon={ico_path}")

    # Paquetes completos y datos requeridos
    packages_to_collect = [
        "keyring",
        "sounddevice",
        "_sounddevice_data",
        "pyaudiowpatch",
        "faster_whisper",
        "ctranslate2",
        "onnxruntime",
        "docx",
        "fitz",
        "pymupdf",
    ]
    for pkg in packages_to_collect:
        cmd.append(f"--collect-all={pkg}")

    # Hidden imports esenciales
    hidden_imports = [
        "keyring.backends.Windows",
        "_portaudiowpatch",
        "groq",
        "google.genai",
        "sqlite3",
        "PySide6.QtCore",
        "PySide6.QtGui",
        "PySide6.QtWidgets",
        "PySide6.QtWebEngineWidgets",
        "PySide6.QtWebEngineCore",
        "PySide6.QtWebEngineQuick",
        "PySide6.QtNetwork",
        "PySide6.QtSvg",
        "PySide6.QtSvgWidgets",
        "PySide6.QtPrintSupport",
    ]
    for hi in hidden_imports:
        cmd.append(f"--hidden-import={hi}")

    # Script principal
    cmd.append(str(main_script))

    print(f"\n[INFO] Ejecutando PyInstaller ({len(cmd)} argumentos)...")
    result = subprocess.run(cmd)

    if result.returncode != 0:
        print(f"\n[ERROR] PyInstaller finalizó con código de error: {result.returncode}")
        return result.returncode

    # 3. Post-procesamiento: Asegurar carpeta assets al nivel raíz de dist/Remodax/
    app_dist_dir = dist_dir / "Remodax"
    dest_assets = app_dist_dir / "assets"
    try:
        if assets_dir.exists():
            if dest_assets.exists():
                shutil.rmtree(dest_assets)
            shutil.copytree(assets_dir, dest_assets)
            print(f"[OK] Carpeta assets sincronizada en: {dest_assets}")
    except Exception as ex:
        print(f"[AVISO] No se pudo copiar assets adicional: {ex}")

    exe_file = app_dist_dir / "Remodax.exe"
    if exe_file.exists():
        size_mb = exe_file.stat().st_size / (1024 * 1024)
        print("==================================================")
        print("  BUILD COMPLETADO EXITOSAMENTE")
        print("==================================================")
        print(f"Ejecutable:     {exe_file}")
        print(f"Tamaño binario: {size_mb:.2f} MB")
        print(f"Carpeta final:  {app_dist_dir}")
        print("==================================================")
        return 0
    else:
        print(f"[ERROR] No se encontró el binario generado en {exe_file}")
        return 1


if __name__ == "__main__":
    sys.exit(build())
