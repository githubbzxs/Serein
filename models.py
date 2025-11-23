"""数据模型定义，包含链类型常量与钱包记录。"""

from dataclasses import dataclass

from config import ChainType


@dataclass
class WalletRecord:
    """单个钱包记录模型，包含链类型与敏感字段。"""

    index: int
    chain_type: str
    network: str
    address: str
    mnemonic: str
    derivation_path: str
    private_key: str

    def is_solana(self) -> bool:
        """是否为 Solana 链记录。"""
        return self.chain_type == ChainType.SOLANA
