# Serein - Web3 批量钱包生成工具

Serein 是一个基于 PyQt5 的本地离线 EVM 钱包批量生成器，用于快速创建独立助记词的钱包地址并导出备份。应用不会联网，也不会自动上传或备份任何敏感信息。

## 功能特点
- 基于 BIP39 助记词与 BIP44 路径（默认 `m/44'/60'/0'/0/{index}`）逐个生成独立钱包。
- 内置常见 EVM 网络（Ethereum / BSC / Polygon / Arbitrum / Optimism / Sepolia），可切换自定义网络名称与 RPC 标记。
- 生成进度实时展示，支持最多 10,000 个地址（可在 `config.py` 中调整）。
- 私钥显示/隐藏一键切换，支持 CSV 导出（UTF-8 with BOM，便于 Excel 打开）。
- 全程离线生成，不依赖外部服务；支持 PyInstaller 打包为桌面可执行文件。

## 环境要求
- Python 3.10+（建议）
- 依赖包：`PyQt5`、`eth-account`、`web3`、`eth-keys`、`mnemonic`

## 安装与运行
```bash
python -m venv .venv
.venv\Scripts\activate       # Windows
pip install -U pip
pip install PyQt5 eth-account web3 eth-keys mnemonic

python main.py               # 启动图形界面
```

## 打包为可执行文件
项目已提供 `Serein.spec`，可直接使用 PyInstaller：
```bash
pyinstaller Serein.spec
```
打包后可执行文件会输出到 `dist/`，临时构建产物在 `build/`。

## 使用步骤
1. 在“批量钱包数量”中填入需要生成的数量（默认 10，最多 10,000）。
2. 选择一个预设网络；如需自定义展示名称/RPC/Chain ID，选择“自定义网路 / RPC”并填写。
3. 点击“开始生成”，等待进度条完成。生成结果会在表格中展示。
4. 通过“显示/隐藏私钥”控制敏感信息的可见性。
5. 需要备份时点击“导出 CSV”，选择保存路径；可用“清空列表”重置当前结果。

## 配置说明
- `config.py` 中的 `PRESET_NETWORKS` 定义了预设网络与自定义入口；`MAX_WALLET_COUNT` 控制单次生成上限；`DERIVATION_PATH_TEMPLATE` 可调整派生路径。
- `wallet_service.py` 负责钱包生成逻辑，使用 `mnemonic` 词表与 `eth-account` 生成地址/私钥。
- `main_window.py` 为 PyQt5 界面与交互逻辑，可根据需要修改 UI 样式或文案。

## 安全与注意事项
- 助记词与私钥仅在本地内存中生成，不会自动备份；请在安全环境中使用并妥善保存导出的文件。
- 不要截图或分享包含助记词/私钥的界面或 CSV；建议在离线或可信网络中操作。
- 大批量生成会消耗一定时间和内存，如需更高数量请分批执行或提升硬件配置。
