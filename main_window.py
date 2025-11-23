"""主窗口与界面逻辑。"""

from typing import List, Optional

from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (
    QApplication,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QStatusBar,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
    QFileDialog,
    QProgressBar,
    QSizePolicy,
)

from config import PRESET_NETWORKS, MAX_WALLET_COUNT
from models import WalletRecord
from wallet_service import generate_wallets, validate_wallet_count, validate_rpc_url


class WalletGeneratorWorker(QThread):
    """后台生成钱包的线程。"""

    progress = pyqtSignal(int, int)
    finished = pyqtSignal(list)
    failed = pyqtSignal(str)

    def __init__(self, count: int, network_name: str, parent=None):
        super().__init__(parent)
        self.count = count
        self.network_name = network_name

    def run(self) -> None:
        try:
            def _cb(done: int) -> None:
                self.progress.emit(done, self.count)

            wallets = generate_wallets(self.count, self.network_name, progress_cb=_cb)
            self.finished.emit(wallets)
        except Exception as exc:  # noqa: BLE001
            self.failed.emit(str(exc))


class MainWindow(QMainWindow):
    """主窗口，负责用户交互与状态展示。"""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Serein - Web3 批量钱包生成器")
        self.setMinimumSize(1100, 760)
        self.setWindowIcon(QIcon())  # 可在打包时替换图标

        self.wallets: List[WalletRecord] = []
        self.show_private_keys = False
        self.worker: Optional[WalletGeneratorWorker] = None

        self._setup_ui()
        self._apply_style()

    def _setup_ui(self) -> None:
        """搭建界面布局。"""
        central = QWidget(self)
        self.setCentralWidget(central)

        main_layout = QVBoxLayout()
        central.setLayout(main_layout)

        title = QLabel("Serein - Web3 钱包批量创建工具")
        title.setObjectName("TitleLabel")
        title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title)

        warning = QLabel("安全提醒：请妥善保管助记词和私钥，不要截图或分享。本工具仅在本地生成，不会自动备份。")
        warning.setWordWrap(True)
        warning.setObjectName("WarningLabel")
        main_layout.addWidget(warning)

        form_box = QGroupBox("生成设置")
        form_layout = QFormLayout()
        form_box.setLayout(form_layout)
        main_layout.addWidget(form_box)

        self.count_input = QSpinBox()
        self.count_input.setRange(1, MAX_WALLET_COUNT)
        self.count_input.setValue(10)
        form_layout.addRow("批量钱包数量", self.count_input)

        self.network_combo = QComboBox()
        for net in PRESET_NETWORKS:
            self.network_combo.addItem(net.name)
        self.network_combo.currentIndexChanged.connect(self._on_network_change)
        form_layout.addRow("选择网络", self.network_combo)

        self.custom_group = QGroupBox("自定义网络配置（可选，仅作标记，不会联网）")
        custom_layout = QFormLayout()
        self.custom_group.setLayout(custom_layout)
        self.custom_name = QLineEdit()
        self.custom_rpc = QLineEdit()
        self.custom_chain_id = QLineEdit()
        self.custom_rpc.setPlaceholderText("https://example.com/rpc")
        self.custom_chain_id.setPlaceholderText("可选")
        custom_layout.addRow("网络名称", self.custom_name)
        custom_layout.addRow("RPC URL", self.custom_rpc)
        custom_layout.addRow("Chain ID", self.custom_chain_id)
        self.custom_group.setVisible(False)
        main_layout.addWidget(self.custom_group)

        btn_layout = QHBoxLayout()
        btn_layout.setAlignment(Qt.AlignLeft)
        main_layout.addLayout(btn_layout)

        self.start_btn = QPushButton("开始生成")
        self.start_btn.clicked.connect(self._start_generation)
        btn_layout.addWidget(self.start_btn)

        self.export_btn = QPushButton("导出为 CSV")
        self.export_btn.clicked.connect(self._export_csv)
        btn_layout.addWidget(self.export_btn)

        self.clear_btn = QPushButton("清空列表")
        self.clear_btn.clicked.connect(self._clear_wallets)
        btn_layout.addWidget(self.clear_btn)

        self.toggle_key_btn = QPushButton("显示私钥")
        self.toggle_key_btn.clicked.connect(self._toggle_private_keys)
        btn_layout.addWidget(self.toggle_key_btn)

        btn_layout.addStretch()

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFixedHeight(22)
        self.progress_bar.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        main_layout.addWidget(self.progress_bar)

        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["序号", "网络", "地址", "助记词", "派生路径", "私钥"])
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setDefaultSectionSize(230)
        self.table.verticalHeader().setVisible(False)
        main_layout.addWidget(self.table)

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self._set_status("本地离线生成，准备就绪")

    def _apply_style(self) -> None:
        """设置界面样式。"""
        style = """
        QWidget {
            font-family: "Microsoft YaHei", "PingFang SC", Arial;
            font-size: 16px;
            color: #1f2d3d;
        }
        #TitleLabel {
            font-size: 24px;
            font-weight: 700;
            padding: 12px;
        }
        #WarningLabel {
            background: #fff7e6;
            border: 1px solid #ffd591;
            border-radius: 10px;
            padding: 12px;
            color: #ad6800;
        }
        QGroupBox {
            border: 1px solid #d9d9d9;
            border-radius: 12px;
            margin-top: 14px;
            padding: 14px;
        }
        QGroupBox:title {
            subcontrol-origin: margin;
            left: 14px;
            padding: 0 6px 0 6px;
            color: #444;
            font-weight: 600;
        }
        QPushButton {
            background-color: #4b7bec;
            border: none;
            color: white;
            padding: 12px 18px;
            border-radius: 9px;
            font-weight: 700;
            font-size: 16px;
        }
        QPushButton:hover {
            background-color: #3a63c7;
        }
        QPushButton:disabled {
            background-color: #a0aec0;
        }
        QTableWidget {
            background: #fafafa;
            border: 1px solid #e5e7eb;
            border-radius: 10px;
            gridline-color: #e5e7eb;
        }
        QHeaderView::section {
            background: #f0f2f5;
            padding: 10px;
            border: none;
            border-right: 1px solid #e5e7eb;
            font-weight: 700;
            font-size: 15px;
        }
        QLineEdit, QSpinBox, QComboBox, QLabel {
            font-size: 15px;
        }
        QLineEdit, QSpinBox, QComboBox {
            border: 1px solid #d9d9d9;
            border-radius: 8px;
            padding: 8px 10px;
        }
        QProgressBar {
            border: 1px solid #d9d9d9;
            border-radius: 8px;
            background: #f5f5f5;
            text-align: center;
            font-size: 14px;
        }
        QProgressBar::chunk {
            background-color: #52c41a;
            border-radius: 8px;
        }
        """
        self.setStyleSheet(style)

    def _on_network_change(self, index: int) -> None:
        """当网络选择变化时，决定是否显示自定义配置。"""
        net = PRESET_NETWORKS[index]
        self.custom_group.setVisible(net.is_custom)

    def _start_generation(self) -> None:
        """启动生成流程。"""
        count = int(self.count_input.value())
        try:
            validate_wallet_count(count, MAX_WALLET_COUNT)
        except ValueError as exc:
            QMessageBox.warning(self, "输入错误", str(exc))
            return

        net = PRESET_NETWORKS[self.network_combo.currentIndex()]
        network_name = net.name
        if net.is_custom:
            network_name = self.custom_name.text().strip() or "自定义网络"
            rpc_url = self.custom_rpc.text().strip()
            if rpc_url and not validate_rpc_url(rpc_url):
                QMessageBox.warning(self, "输入错误", "RPC URL 格式不正确，请使用 http/https 开头。")
                return

        self.start_btn.setEnabled(False)
        self._set_status("正在生成，请稍候…（离线本地生成，每个钱包独立助记词）")
        self.progress_bar.setRange(0, count)
        self.progress_bar.setValue(0)

        self.worker = WalletGeneratorWorker(count, network_name)
        self.worker.progress.connect(self._on_progress)
        self.worker.finished.connect(self._on_finished)
        self.worker.failed.connect(self._on_failed)
        self.worker.start()

    def _on_progress(self, done: int, total: int) -> None:
        """更新进度条。"""
        self.progress_bar.setValue(done)
        self._set_status(f"正在生成 {done}/{total}（离线）")

    def _on_finished(self, wallets: List[WalletRecord]) -> None:
        """生成完成后处理数据。"""
        self.wallets = wallets
        self._refresh_table()
        self._set_status(f"生成完成，共 {len(wallets)} 个。（离线）")
        self.start_btn.setEnabled(True)
        self.worker = None

    def _on_failed(self, message: str) -> None:
        """错误处理。"""
        QMessageBox.critical(self, "生成失败", message)
        self._set_status("生成失败")
        self.start_btn.setEnabled(True)
        self.worker = None

    def _refresh_table(self) -> None:
        """根据当前钱包列表刷新表格。"""
        self.table.setRowCount(len(self.wallets))
        for row, w in enumerate(self.wallets):
            items = [
                QTableWidgetItem(str(w.index)),
                QTableWidgetItem(w.network),
                QTableWidgetItem(w.address),
                QTableWidgetItem(w.mnemonic),
                QTableWidgetItem(w.derivation_path),
                QTableWidgetItem(self._mask_value(w.private_key)),
            ]
            for col, item in enumerate(items):
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.table.setItem(row, col, item)
        self.table.resizeColumnsToContents()
        self.table.horizontalHeader().setStretchLastSection(True)

    def _mask_value(self, value: str) -> str:
        """根据开关返回显示值。"""
        if self.show_private_keys:
            return value
        return "**************"

    def _toggle_private_keys(self) -> None:
        """切换私钥显示状态。"""
        self.show_private_keys = not self.show_private_keys
        self.toggle_key_btn.setText("隐藏私钥" if self.show_private_keys else "显示私钥")
        # 刷新私钥列
        for row, w in enumerate(self.wallets):
            item = self.table.item(row, 5)
            if item:
                item.setText(self._mask_value(w.private_key))

    def _export_csv(self) -> None:
        """导出为 CSV 文件。"""
        if not self.wallets:
            QMessageBox.information(self, "提示", "当前没有可导出的钱包记录。")
            return
        path, _ = QFileDialog.getSaveFileName(self, "导出 CSV", "wallets.csv", "CSV Files (*.csv)")
        if not path:
            return
        try:
            import csv

            with open(path, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerow(["序号", "网络", "地址", "助记词", "派生路径", "私钥"])
                for w in self.wallets:
                    writer.writerow([w.index, w.network, w.address, w.mnemonic, w.derivation_path, w.private_key])
            QMessageBox.information(self, "导出成功", f"已导出到 {path}")
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "导出失败", str(exc))

    def _clear_wallets(self) -> None:
        """清空列表。"""
        self.wallets = []
        self.table.setRowCount(0)
        self.progress_bar.setValue(0)
        self._set_status("已清空列表")

    def _set_status(self, text: str) -> None:
        """更新底部状态文本。"""
        self.status_bar.showMessage(text)


def run_app() -> None:
    """启动应用入口。"""
    import sys

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
