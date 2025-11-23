"""数据模型定义。"""

from dataclasses import dataclass


@dataclass
class WalletRecord:
    """单个钱包记录模型。"""

    index: int
    network: str
    address: str
    mnemonic: str
    derivation_path: str
    private_key: str
