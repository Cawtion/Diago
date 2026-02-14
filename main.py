"""
Diago -- Automotive Audio Diagnostic Analyzer
Main application entry point.
"""

import logging
import sys
import os

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

from core.config import get_settings
from gui.main_window import MainWindow
from database.db_manager import DatabaseManager

logger = logging.getLogger(__name__)


def _setup_logging() -> None:
    """Configure application-wide logging."""
    settings = get_settings()
    level = logging.DEBUG if settings.debug else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    # Quiet noisy third-party loggers
    logging.getLogger("matplotlib").setLevel(logging.WARNING)
    logging.getLogger("PIL").setLevel(logging.WARNING)


def main():
    """Initialize and launch the application."""
    _setup_logging()

    settings = get_settings()
    logger.info("Starting %s v%s", settings.app_name, settings.app_version)

    # High DPI scaling
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"

    app = QApplication(sys.argv)
    app.setApplicationName(settings.app_name)
    app.setOrganizationName("AutoAudioDiagnostics")

    # Apply a modern dark stylesheet
    app.setStyleSheet(get_stylesheet())

    # Initialize the database (creates tables and seeds data if needed)
    db_path = settings.db_path
    logger.info("Database path: %s", db_path)
    db_manager = DatabaseManager(db_path, settings.obd2_codes_path)
    db_manager.initialize()

    # Create and show the main window
    window = MainWindow(db_manager)
    window.show()

    sys.exit(app.exec())


def get_stylesheet():
    """Return the application-wide dark stylesheet."""
    return """
        QMainWindow {
            background-color: #1e1e2e;
        }
        QWidget {
            background-color: #1e1e2e;
            color: #cdd6f4;
            font-family: "Segoe UI", "Arial", sans-serif;
            font-size: 13px;
        }
        QPushButton {
            background-color: #45475a;
            color: #cdd6f4;
            border: 1px solid #585b70;
            border-radius: 6px;
            padding: 8px 16px;
            font-weight: bold;
            min-height: 20px;
        }
        QPushButton:hover {
            background-color: #585b70;
            border-color: #89b4fa;
        }
        QPushButton:pressed {
            background-color: #313244;
        }
        QPushButton:disabled {
            background-color: #313244;
            color: #585b70;
        }
        QPushButton#recordBtn {
            background-color: #a6e3a1;
            color: #1e1e2e;
        }
        QPushButton#recordBtn:hover {
            background-color: #94e2d5;
        }
        QPushButton#stopBtn {
            background-color: #f38ba8;
            color: #1e1e2e;
        }
        QPushButton#stopBtn:hover {
            background-color: #eba0ac;
        }
        QPushButton#analyzeBtn {
            background-color: #89b4fa;
            color: #1e1e2e;
            font-size: 14px;
            padding: 10px 24px;
        }
        QPushButton#analyzeBtn:hover {
            background-color: #b4d0fb;
        }
        QLineEdit {
            background-color: #313244;
            color: #cdd6f4;
            border: 1px solid #585b70;
            border-radius: 4px;
            padding: 6px 10px;
        }
        QLineEdit:focus {
            border-color: #89b4fa;
        }
        QComboBox {
            background-color: #313244;
            color: #cdd6f4;
            border: 1px solid #585b70;
            border-radius: 4px;
            padding: 6px 10px;
        }
        QComboBox::drop-down {
            border: none;
        }
        QComboBox QAbstractItemView {
            background-color: #313244;
            color: #cdd6f4;
            selection-background-color: #45475a;
        }
        QLabel {
            color: #cdd6f4;
        }
        QLabel#sectionHeader {
            font-size: 15px;
            font-weight: bold;
            color: #89b4fa;
            padding: 4px 0px;
        }
        QGroupBox {
            border: 1px solid #45475a;
            border-radius: 8px;
            margin-top: 12px;
            padding-top: 16px;
            font-weight: bold;
            color: #89b4fa;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 12px;
            padding: 0 6px;
        }
        QScrollArea {
            border: none;
        }
        QStatusBar {
            background-color: #181825;
            color: #a6adc8;
        }
        QMenuBar {
            background-color: #181825;
            color: #cdd6f4;
        }
        QMenuBar::item:selected {
            background-color: #45475a;
        }
        QMenu {
            background-color: #313244;
            color: #cdd6f4;
        }
        QMenu::item:selected {
            background-color: #45475a;
        }
        QTextEdit {
            background-color: #313244;
            color: #cdd6f4;
            border: 1px solid #585b70;
            border-radius: 4px;
            padding: 6px 10px;
        }
        QTextEdit:focus {
            border-color: #89b4fa;
        }
        QTabWidget::pane {
            border: 1px solid #45475a;
        }
        QTabBar::tab {
            background: #313244;
            color: #a6adc8;
            padding: 6px 16px;
        }
        QTabBar::tab:selected {
            background: #1e1e2e;
            color: #89b4fa;
            font-weight: bold;
        }
    """


if __name__ == "__main__":
    main()
