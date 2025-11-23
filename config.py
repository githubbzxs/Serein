"""全局配置，提供预设网络、派生路径模板与用户设置文件路径。"""

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional


class ChainType:
    """链类型字符串枚举，便于界面区分 EVM 与 Solana。"""

    EVM = "EVM"
    SOLANA = "Solana"


@dataclass
class NetworkConfig:
    """网络配置模型，支持预设与自定义网络。"""

    name: str
    chain_type: str
    rpc_url: Optional[str] = None
    chain_id: Optional[int] = None
    is_custom: bool = False
    derivation_path_template: Optional[str] = None


# 默认 BIP44 派生路径模板
DERIVATION_PATH_TEMPLATE_EVM = "m/44'/60'/0'/0/{index}"
# Solana 采用全硬化路径，默认形式 m/44'/501'/0'/0'/{index}'
DERIVATION_PATH_TEMPLATE_SOL = "m/44'/501'/0'/0'/{index}'"

# 预设网络列表，覆盖常用 EVM 与 Solana 环境
PRESET_NETWORKS: List[NetworkConfig] = [
    NetworkConfig(name="Ethereum", chain_type=ChainType.EVM, rpc_url="https://rpc.ankr.com/eth", chain_id=1),
    NetworkConfig(name="BNB Smart Chain", chain_type=ChainType.EVM, rpc_url="https://rpc.ankr.com/bsc", chain_id=56),
    NetworkConfig(name="Polygon", chain_type=ChainType.EVM, rpc_url="https://rpc.ankr.com/polygon", chain_id=137),
    NetworkConfig(name="Arbitrum One", chain_type=ChainType.EVM, rpc_url="https://rpc.ankr.com/arbitrum", chain_id=42161),
    NetworkConfig(name="Optimism", chain_type=ChainType.EVM, rpc_url="https://rpc.ankr.com/optimism", chain_id=10),
    NetworkConfig(name="Sepolia Testnet", chain_type=ChainType.EVM, rpc_url="https://rpc.ankr.com/eth_sepolia", chain_id=11155111),
    NetworkConfig(
        name="Solana",
        chain_type=ChainType.SOLANA,
        rpc_url="https://api.mainnet-beta.solana.com",
        derivation_path_template=DERIVATION_PATH_TEMPLATE_SOL,
    ),
    NetworkConfig(
        name="Solana Devnet",
        chain_type=ChainType.SOLANA,
        rpc_url="https://api.devnet.solana.com",
        derivation_path_template=DERIVATION_PATH_TEMPLATE_SOL,
    ),
    NetworkConfig(
        name="Custom Network / RPC",
        chain_type=ChainType.EVM,
        is_custom=True,
        derivation_path_template=DERIVATION_PATH_TEMPLATE_EVM,
    ),
]

# 允许的最大批量生成数量
MAX_WALLET_COUNT = 10000

# 主题与设置存储位置
DEFAULT_THEME = "light"
USER_SETTINGS_FILE = Path("user_settings.json")
