"""主窗口与界面逻辑，包含生成、复制与主题切换。"""

from typing import List, Optional

from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (
    QApplication,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QStatusBar,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
    QProgressBar,
    QSizePolicy,
)

from config import MAX_WALLET_COUNT, PRESET_NETWORKS, ChainType, NetworkConfig
from models import WalletRecord
from theme_manager import ThemeName, apply_theme, save_theme
from wallet_service import generate_wallets, validate_wallet_count, validate_rpc_url


class WalletGeneratorWorker(QThread):
    """后台生成钱包的线程，避免阻塞 UI。"""

    progress = pyqtSignal(int, int)
    finished = pyqtSignal(list)
    failed = pyqtSignal(str)

    def __init__(self, count: int, network: NetworkConfig, parent=None):
        super().__init__(parent)
        self.count = count
        self.network = network

    def run(self) -> None:
        try:
            def _cb(done: int) -> None:
                self.progress.emit(done, self.count)

            wallets = generate_wallets(self.count, self.network, progress_cb=_cb)
            self.finished.emit(wallets)
        except Exception as exc:  # noqa: BLE001
            self.failed.emit(str(exc))


class MainWindow(QMainWindow):
    """主窗口，负责用户交互与状态展示。"""

    def __init__(self, app: QApplication, current_theme: ThemeName) -> None:
        super().__init__()
        self.app = app
        self.current_theme: ThemeName = current_theme
        self.wallets: List[WalletRecord] = []
        self.show_private_keys = False
        self.worker: Optional[WalletGeneratorWorker] = None

        self.setWindowTitle("Serein - Web3 钱包批量创建器")
        self.setMinimumSize(1200, 820)
        self.setWindowIcon(QIcon())  # 可在打包时替换为品牌图标

        self._setup_ui()
        self._init_menu()
        self._set_status("本地离线生成，准备就绪")

    # ------------------------- UI 构建 ------------------------- #
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

        warning = QLabel("安全提醒：请妥善保管助记词与私钥/密钥，不要截图或分享。本工具仅在本地生成，不会上传或联网。")
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

        self.theme_toggle_btn = QPushButton()
        self.theme_toggle_btn.clicked.connect(self._toggle_theme_button)
        btn_layout.addWidget(self.theme_toggle_btn)
        self._update_theme_toggle_text()

        btn_layout.addStretch()

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFixedHeight(22)
        self.progress_bar.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        main_layout.addWidget(self.progress_bar)

        self.table = QTableWidget(0, 8)
        self.table.setHorizontalHeaderLabels(
            ["操作", "序号", "链类型", "网络", "地址", "助记词", "派生路径", "私钥/密钥"]
        )
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setDefaultSectionSize(210)
        self.table.verticalHeader().setVisible(False)
        main_layout.addWidget(self.table)

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

    def _init_menu(self) -> None:
        """初始化菜单栏（主题切换）。"""
        menu_bar = self.menuBar()
        view_menu: QMenu = menu_bar.addMenu("视图")
        theme_menu = view_menu.addMenu("主题")

        self.light_action = theme_menu.addAction("浅色模式")
        self.dark_action = theme_menu.addAction("深色模式")
        self.light_action.setCheckable(True)
        self.dark_action.setCheckable(True)

        self.light_action.triggered.connect(lambda: self._switch_theme("light"))
        self.dark_action.triggered.connect(lambda: self._switch_theme("dark"))

        self._refresh_theme_actions()

    # ------------------------- 事件与逻辑 ------------------------- #
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
        network_to_use = net
        if net.is_custom:
            name = self.custom_name.text().strip() or "Custom Network"
            rpc_url = self.custom_rpc.text().strip()
            chain_id_text = self.custom_chain_id.text().strip()
            if rpc_url and not validate_rpc_url(rpc_url):
                QMessageBox.warning(self, "输入错误", "RPC URL 格式不正确，请使用 http/https 开头。")
                return
            chain_id = int(chain_id_text) if chain_id_text.isdigit() else None
            network_to_use = NetworkConfig(
                name=name,
                chain_type=ChainType.EVM,
                rpc_url=rpc_url or None,
                chain_id=chain_id,
                is_custom=True,
                derivation_path_template=net.derivation_path_template,
            )

        self.start_btn.setEnabled(False)
        self._set_status("正在生成，请稍候…（离线本地生成，每个钱包独立助记词）")
        self.progress_bar.setRange(0, count)
        self.progress_bar.setValue(0)

        self.worker = WalletGeneratorWorker(count, network_to_use)
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
            # 操作列：复制按钮置于最左列
            action_cell = self._build_action_buttons(row)
            self.table.setCellWidget(row, 0, action_cell)

            items = [
                (1, QTableWidgetItem(str(w.index))),
                (2, QTableWidgetItem(self._display_chain_type(w.chain_type))),
                (3, QTableWidgetItem(w.network)),
                (4, QTableWidgetItem(w.address)),
                (5, QTableWidgetItem(w.mnemonic)),
                (6, QTableWidgetItem(w.derivation_path)),
                (7, QTableWidgetItem(self._mask_value(w.private_key))),
            ]
            for col, item in items:
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.table.setItem(row, col, item)

        self.table.resizeColumnsToContents()
        self.table.horizontalHeader().setStretchLastSection(True)

    def _build_action_buttons(self, row: int) -> QWidget:
        """为指定行创建复制按钮组。"""
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        btn_addr = QPushButton("复制地址")
        btn_addr.setToolTip("复制钱包地址到剪贴板")
        btn_addr.setProperty("row", row)
        btn_addr.clicked.connect(lambda _, r=row: self._copy_field(r, "address"))
        layout.addWidget(btn_addr)

        btn_mnemonic = QPushButton("复制助记词")
        btn_mnemonic.setToolTip("复制助记词，请勿泄露")
        btn_mnemonic.setProperty("row", row)
        btn_mnemonic.clicked.connect(lambda _, r=row: self._copy_field(r, "mnemonic"))
        layout.addWidget(btn_mnemonic)

        btn_priv = QPushButton("复制私钥")
        btn_priv.setToolTip("复制私钥/密钥，注意保密")
        btn_priv.setProperty("row", row)
        btn_priv.clicked.connect(lambda _, r=row: self._copy_field(r, "private_key"))
        layout.addWidget(btn_priv)

        layout.addStretch()
        return container

    def _copy_field(self, row: int, field: str) -> None:
        """将指定行的字段复制到剪贴板。"""
        if row >= len(self.wallets):
            return
        wallet = self.wallets[row]
        value = getattr(wallet, field, "")
        QApplication.clipboard().setText(value)
        if field == "address":
            msg = "地址已复制到剪贴板"
        elif field == "mnemonic":
            msg = "助记词已复制，请注意保密"
        else:
            msg = "私钥/密钥已复制，请勿泄露"
        self._set_status(msg)

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
            item = self.table.item(row, 7)
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
                writer.writerow(["序号", "链类型", "网络", "地址", "助记词", "派生路径", "私钥/密钥"])
                for w in self.wallets:
                    writer.writerow(
                        [
                            w.index,
                            self._display_chain_type(w.chain_type),
                            w.network,
                            w.address,
                            w.mnemonic,
                            w.derivation_path,
                            w.private_key,
                        ]
                    )
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
        self.status_bar.showMessage(text, 3000)

    # ------------------------- 主题 ------------------------- #
    def _switch_theme(self, theme: ThemeName) -> None:
        """切换主题并持久化。"""
        if theme == self.current_theme:
            return
        self.current_theme = theme
        apply_theme(self.app, theme)
        save_theme(theme)
        self._refresh_theme_actions()
        self._set_status("已切换为深色模式" if theme == "dark" else "已切换为浅色模式")
        self._update_theme_toggle_text()

    def _refresh_theme_actions(self) -> None:
        """同步菜单勾选状态。"""
        self.light_action.setChecked(self.current_theme == "light")
        self.dark_action.setChecked(self.current_theme == "dark")

    @staticmethod
    def _display_chain_type(chain_type: str) -> str:
        """将内部链类型值转换为中文标签。"""
        return "Solana 链" if chain_type == ChainType.SOLANA else "EVM 链"

    def _update_theme_toggle_text(self) -> None:
        """根据当前主题更新切换按钮文本。"""
        if self.current_theme == "dark":
            self.theme_toggle_btn.setText("切换到浅色模式")
        else:
            self.theme_toggle_btn.setText("切换到深色模式")

    def _toggle_theme_button(self) -> None:
        """按钮触发的主题切换入口。"""
        target = "light" if self.current_theme == "dark" else "dark"
        self._switch_theme(target)
