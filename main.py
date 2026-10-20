"""
Remodax - Application Entrypoint
Initializes Dependency Injection Container, PySide6 GUI runtime, and event loop.
"""

import sys
from pathlib import Path

# Ensure root directory is on PYTHONPATH (only when running from source in development)
if not getattr(sys, "frozen", False):
    ROOT_DIR = Path(__file__).resolve().parent
    if str(ROOT_DIR) not in sys.path:
        sys.path.insert(0, str(ROOT_DIR))

    venv_site_packages = ROOT_DIR / "venv" / "Lib" / "site-packages"
    if venv_site_packages.exists() and str(venv_site_packages) not in sys.path:
        sys.path.insert(0, str(venv_site_packages))

from src.container import AppContainer


def main() -> int:
    """Main application lifecycle runner."""
    # 1. Initialize Dependency Container (Filesystem, SQLite, Windows Credential Manager)
    container = AppContainer()
    logger = container.logger

    logger.info("Iniciando aplicación %s...", container.config.app_name)

    # Fast headless smoke verification for automated CI / packaging tests
    if "--check" in sys.argv:
        logger.info("Verificación de arranque completada con éxito.")
        return 0

    try:
        from PySide6.QtWidgets import QApplication
        from src.ui.main_window import MainWindow

        # Enable High-DPI scaling
        app = QApplication(sys.argv)
        app.setApplicationName(container.config.app_name)
        app.setOrganizationName("RemodaxCorp")

        # Launch UI Shell
        window = MainWindow(container)
        window.show()

        logger.info("Bucle de eventos de interfaz gráfica iniciado.")
        return app.exec()

    except ImportError as ex:
        logger.error(
            "Falta una dependencia requerida para la interfaz gráfica: %s. "
            "Por favor ejecuta: pip install -r requirements.txt",
            str(ex)
        )
        return 1
    except Exception as ex:
        logger.critical("Error fatal al iniciar la aplicación: %s", str(ex), exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
