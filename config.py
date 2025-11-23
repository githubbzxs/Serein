"""全局配置，提供预设网络列表与默认常量。"""

from dataclasses import dataclass
from typing import Optional, List


@dataclass
class NetworkConfig:
    """EVM 网络配置模型。"""

    name: str
    rpc_url: Optional[str] = None
    chain_id: Optional[int] = None
    is_custom: bool = False


# 预设的常用网络列表
PRESET_NETWORKS: List[NetworkConfig] = [
    NetworkConfig(name="Ethereum Mainnet", rpc_url="https://rpc.ankr.com/eth", chain_id=1),
    NetworkConfig(name="BNB Smart Chain", rpc_url="https://rpc.ankr.com/bsc", chain_id=56),
    NetworkConfig(name="Polygon", rpc_url="https://rpc.ankr.com/polygon", chain_id=137),
    NetworkConfig(name="Arbitrum", rpc_url="https://rpc.ankr.com/arbitrum", chain_id=42161),
    NetworkConfig(name="Optimism", rpc_url="https://rpc.ankr.com/optimism", chain_id=10),
    NetworkConfig(name="Sepolia Testnet", rpc_url="https://rpc.ankr.com/eth_sepolia", chain_id=11155111),
    NetworkConfig(name="自定义网络 / RPC", is_custom=True),
]


# 默认的 BIP44 派生路径模板
DERIVATION_PATH_TEMPLATE = "m/44'/60'/0'/0/{index}"

# 允许的最大批量生成数量
MAX_WALLET_COUNT = 10000
