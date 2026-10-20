# Remodax - Asistente de Entrevistas y RAG Documental

**Remodax** es una aplicación de escritorio para Windows 10 y 11 construida con **Python** y **PySide6**, diseñada bajo principios de **Clean Architecture** y ciberseguridad avanzada. Permite transcribir audio del sistema o micrófono en tiempo real, consultar documentos privados locales (PDF y Word) mediante RAG y generar respuestas inmediatas con modelos de lenguaje ultrarrápidos (GroqCloud y Gemini API).

---

## 🚀 Características Principales

- **Interfaz Moderna con Tema Oscuro:** Diseñada en PySide6 (Qt para Python) con navegación fluida, componentes modulares y diseño ergonómico para largas sesiones.
- **Audio WASAPI Loopback y Micrófono:** Captura audio del sistema o de hardware de entrada en Windows.
- **Transcripción Inteligente (Speech-To-Text):** Basada en Whisper (`faster-whisper`), operando en memoria sin persistir audio en disco.
- **Generación Ultrarrápida con IA:** Conectores nativos con streaming para GroqCloud (`llama-3.3-70b-versatile`) y Google Gemini (`gemini-2.5-flash`).
- **RAG Local y Privado:** Procesamiento de archivos PDF (PyMuPDF) y Word (python-docx) con motor de recuperación completamente local y fuera de la nube.
- **Seguridad y Ciberseguridad Reforzada:**
  - Almacenamiento de API Keys exclusivamente en **Windows Credential Manager** (`keyring`).
  - Cero persistencia de claves en código, logs o bases de datos SQLite.
  - Enmascaramiento permanente de credenciales en pantalla (`gsk_••••••••1234`).
  - Autorización explícita requerida antes de enviar fragmentos de documentos a APIs externas.
  - Cero grabaciones de audio en disco por defecto.
- **Almacenamiento Local Seguro:** SQLite para historial de preguntas/respuestas y metadatos de configuración sin datos sensibles.
- **Empaquetado para Windows:** Script de construcción con PyInstaller para generar el ejecutable `.exe`.

---

## 📂 Estructura del Proyecto

```text
Remodax/
├── .gitignore                      # Exclusión estricta de secretos, dbs, audio y documentos
├── README.md                       # Documentación principal
├── pyproject.toml                  # Configuración del paquete y metadatos
├── requirements.txt                # Dependencias del proyecto
├── main.py                         # Punto de entrada de la aplicación
├── assets/
│   ├── icons/                      # Recursos visuales e iconos
│   └── styles/
│       └── dark_theme.qss          # Hoja de estilos del tema oscuro
├── docs/
│   ├── architecture.md             # Diagramas y desglose de Clean Architecture & SOLID
│   ├── security.md                 # Especificación de ciberseguridad y privacidad
│   └── modules_roadmap.md          # Estado de módulos y hoja de ruta
├── scripts/
│   ├── build_exe.py                # Compilación a binario ejecutable con PyInstaller
│   └── setup_env.bat               # Script batch para inicializar entorno en Windows
├── tests/                          # Pruebas unitarias herméticas y fixtures
│   ├── conftest.py
│   ├── test_domain_entities.py
│   ├── test_security.py
│   └── test_use_cases.py
└── src/
    ├── container.py                # Contenedor de Inyección de Dependencias
    ├── config/                     # Rutas, constantes y filtro de sanitización de logs
    ├── domain/                     # Núcleo: Entidades, Puertos (Interfaces) y Excepciones
    │   ├── entities/
    │   └── ports/
    ├── application/                # Casos de uso y DTOs
    │   ├── dtos/
    │   └── use_cases/
    ├── infrastructure/             # Adaptadores de tecnologías externas
    │   ├── security/               # Windows Credential Manager (keyring)
    │   ├── audio/                  # WASAPI Loopback y Whisper
    │   ├── ai/                     # Clientes Groq y Gemini con streaming
    │   ├── documents/              # Parsers PDF (PyMuPDF), Word (python-docx) y RAG local
    │   └── storage/                # SQLite Database y Repositorios
    └── ui/                         # Interfaz gráfica PySide6 (MVVM)
        ├── components/             # Sidebar, MaskedInput, StatusBadge
        ├── view_models/            # ViewModels multihilo con Señales de Qt
        ├── views/                  # Vistas (Entrevistas, Documentos, API Keys, Historial, Config)
        └── main_window.py          # Ventana principal
```

---

## 🛠️ Instalación y Configuración

### 1. Requisitos Previos
- **Sistema Operativo:** Windows 10 o Windows 11 (64-bit).
- **Python:** Versión 3.10 o superior (verificado con Python 3.14).

### 2. Creación del Entorno Virtual
Desde la raíz del proyecto en PowerShell o CMD:
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```
*(O ejecuta directamente `scripts\setup_env.bat`)*

### 3. Instalación de Dependencias
```powershell
pip install -r requirements.txt
```

### 4. Ejecución de la Aplicación
```powershell
python main.py
```

### 5. Ejecución de Pruebas Unitarias
```powershell
pytest -v
```

### 6. Generación del Ejecutable `.exe`
```powershell
python scripts\build_exe.py
```

---

## 🔒 Consideraciones de Seguridad

1. **Nunca incluyas API Keys en el repositorio:** Al ejecutar Remodax por primera vez, ingresa tus claves en la pestaña **Configuración API**. El sistema las guardará automáticamente en el almacén cifrado de Windows.
2. **Control de RAG:** Para que la IA utilice información de tus documentos importados, marca la casilla correspondiente en cada consulta o habilítala por defecto en Configuración.
