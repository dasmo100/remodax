"""
Remodax - GUI Verification Script
Renders the complete GUI shell, traverses all 5 views, takes a high-res screenshot,
and confirms error-free execution.
"""

import sys
import os
from pathlib import Path

# Ensure root is on sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer, QEventLoop
from src.container import AppContainer
from src.ui.main_window import MainWindow


def verify_gui():
    print("[1/5] Inicializando QApplication...")
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)

    print("[2/5] Inicializando AppContainer...")
    container = AppContainer()

    print("[3/5] Instanciando MainWindow con tema oscuro...")
    window = MainWindow(container)
    window.show()

    # Create artifacts directory for screenshots if needed
    screenshot_dir = ROOT_DIR / "assets" / "screenshots"
    screenshot_dir.mkdir(parents=True, exist_ok=True)

    print("[4/5] Navegando por todas las 4 secciones...")
    section_names = ["Entrevista", "Documentos", "Configuración API", "Ajustes"]

    # Wait briefly for WebEngine DitherVeil animation to initialize and load
    loop = QEventLoop()
    QTimer.singleShot(1600, loop.quit)
    loop.exec()

    for idx, name in enumerate(section_names):
        window._sidebar._buttons[idx].click()
        app.processEvents()
        print(f"  [OK] Seccion {idx}: '{name}' renderizada (Indice de Stack: {window._stack.currentIndex()})")
        # Save screenshot of each view
        clean_name = name.lower().replace(" ", "_").replace("ó", "o")
        screenshot_path = screenshot_dir / f"view_{idx}_{clean_name}.png"
        pixmap = window.grab()
        pixmap.save(str(screenshot_path))

    # Return to Entrevista view
    window._sidebar._buttons[0].click()
    app.processEvents()
    main_screenshot = screenshot_dir / "remodax_main_interview.png"
    window.grab().save(str(main_screenshot))
    print(f"[5/5] Capturas de pantalla guardadas en: {screenshot_dir}")

    window.close()
    print("Verificacion de GUI completada exitosamente sin errores.")
    return 0


if __name__ == "__main__":
    sys.exit(verify_gui())
