"""主题管理：提供浅色/深色 QSS 与持久化。"""

import json
from pathlib import Path
from typing import Literal

from PyQt5.QtWidgets import QApplication

from config import DEFAULT_THEME, USER_SETTINGS_FILE

ThemeName = Literal["light", "dark"]

# 基础字体与控件圆角
BASE_QSS = """
* {
    font-family: "Microsoft YaHei", "PingFang SC", Arial;
    font-size: 15px;
}
#TitleLabel {
    font-size: 24px;
    font-weight: 700;
    padding: 12px;
}
#WarningLabel {
    border-radius: 10px;
    padding: 12px;
    font-size: 14px;
}
QGroupBox {
    border-radius: 12px;
    margin-top: 14px;
    padding: 14px;
}
QGroupBox:title {
    subcontrol-origin: margin;
    left: 14px;
    padding: 0 6px;
    font-weight: 600;
}
QPushButton {
    border: none;
    padding: 10px 14px;
    border-radius: 8px;
    font-weight: 600;
}
QPushButton:disabled {
    opacity: 0.6;
}
QLineEdit, QSpinBox, QComboBox {
    border-radius: 8px;
    padding: 8px 10px;
}
QHeaderView::section {
    padding: 8px 10px;
    font-weight: 700;
    font-size: 14px;
}
QTableWidget {
    border-radius: 10px;
}
QStatusBar {
    padding-left: 8px;
}
"""

LIGHT_QSS = """
QWidget { background: #f7f8fa; color: #1f2d3d; }
#WarningLabel { background: #fff7e6; border: 1px solid #ffd591; color: #ad6800; }
QGroupBox { border: 1px solid #d9d9d9; background: #ffffff; }
QGroupBox:title { color: #555; }
QPushButton { background-color: #4b7bec; color: white; }
QPushButton:hover { background-color: #3a63c7; }
QLineEdit, QSpinBox, QComboBox { border: 1px solid #d9d9d9; background: #ffffff; }
QTableWidget { background: #ffffff; border: 1px solid #e5e7eb; gridline-color: #e5e7eb; }
QHeaderView::section { background: #f0f2f5; border: 1px solid #e5e7eb; }
QProgressBar { border: 1px solid #d9d9d9; background: #f5f5f5; text-align: center; }
QProgressBar::chunk { background-color: #52c41a; border-radius: 8px; }
QScrollBar:vertical { background: #f0f2f5; width: 12px; }
QScrollBar::handle:vertical { background: #cbd5e1; border-radius: 6px; min-height: 24px; }
QStatusBar { background: #eef2f7; color: #1f2d3d; }
"""

DARK_QSS = """
QWidget { background: #1b1f2a; color: #e8ebf0; }
#WarningLabel { background: #2a3242; border: 1px solid #3f4a60; color: #e3ad63; }
QGroupBox { border: 1px solid #2f3849; background: #202532; }
QGroupBox:title { color: #d7deea; }
QPushButton { background-color: #3a7bd5; color: #e8ebf0; }
QPushButton:hover { background-color: #2f68b3; }
QLineEdit, QSpinBox, QComboBox { border: 1px solid #3b455a; background: #1f2533; color: #e8ebf0; }
QTableWidget { background: #161b26; border: 1px solid #2f3849; gridline-color: #2f3849; }
QHeaderView::section { background: #202836; border: 1px solid #2f3849; color: #d7deea; }
QTableWidget::item:selected { background: #2f68b3; color: #ffffff; }
QProgressBar { border: 1px solid #3b455a; background: #1f2533; text-align: center; color: #d7deea; }
QProgressBar::chunk { background-color: #52c41a; border-radius: 8px; }
QScrollBar:vertical { background: #1f2533; width: 12px; }
QScrollBar::handle:vertical { background: #3a4a63; border-radius: 6px; min-height: 24px; }
QStatusBar { background: #141821; color: #d7deea; }
"""


def load_theme(settings_path: Path = USER_SETTINGS_FILE) -> ThemeName:
    """从本地配置读取主题名；若不存在则返回默认主题。"""
    try:
        data = json.loads(settings_path.read_text(encoding="utf-8"))
        theme = data.get("theme", DEFAULT_THEME)
        if theme in ("light", "dark"):
            return theme  # type: ignore[return-value]
    except FileNotFoundError:
        pass
    except Exception:
        # 配置损坏时忽略，走默认
        pass
    return DEFAULT_THEME  # type: ignore[return-value]


def save_theme(theme: ThemeName, settings_path: Path = USER_SETTINGS_FILE) -> None:
    """将主题名写入本地配置，便于下次启动还原。"""
    settings = {"theme": theme}
    settings_path.write_text(json.dumps(settings, ensure_ascii=False, indent=2), encoding="utf-8")


def build_stylesheet(theme: ThemeName) -> str:
    """组合基础 QSS 与主题色系。"""
    if theme == "dark":
        return BASE_QSS + DARK_QSS
    return BASE_QSS + LIGHT_QSS


def apply_theme(app: QApplication, theme: ThemeName) -> None:
    """将主题样式表应用到 QApplication。"""
    app.setStyleSheet(build_stylesheet(theme))
