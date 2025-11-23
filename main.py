"""应用入口，负责启动 QApplication 并加载主题。"""

import sys

from PyQt5.QtWidgets import QApplication

from theme_manager import apply_theme, load_theme
from ui_main_window import MainWindow


def run_app() -> None:
    """启动 Serein 主窗口。"""
    app = QApplication(sys.argv)
    theme = load_theme()
    apply_theme(app, theme)

    window = MainWindow(app=app, current_theme=theme)
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    run_app()
