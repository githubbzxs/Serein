"""钱包生成与校验服务。"""

import hashlib
import hmac
from typing import Callable, List, Optional, Tuple

from eth_account import Account
from eth_keys import constants as eth_constants
from eth_keys import keys as eth_keys
from mnemonic import Mnemonic
from web3 import Web3

from config import DERIVATION_PATH_TEMPLATE
from models import WalletRecord

# 启用 HD 钱包支持（eth-account 默认关闭，需要显式允许）
Account.enable_unaudited_hdwallet_features()

# 使用标准 BIP39 英文词表的生成器
MNEMONIC_GEN = Mnemonic("english")

# 曲线阶常量
SECP256K1_N = eth_constants.SECPK1_N


def validate_wallet_count(count: int, max_count: int) -> None:
    """校验批量数量是否合法。"""
    if count <= 0:
        raise ValueError("数量必须为正整数")
    if count > max_count:
        raise ValueError(f"数量过大，建议不超过 {max_count}")


def validate_rpc_url(url: str) -> bool:
    """基础格式校验 RPC URL。"""
    if not url:
        return False
    return url.startswith("http://") or url.startswith("https://")


def _generate_mnemonic(num_words: int = 12) -> str:
    """使用标准 BIP39 词表生成助记词。"""
    mapping = {12: 128, 15: 160, 18: 192, 21: 224, 24: 256}
    if num_words not in mapping:
        raise ValueError("助记词长度仅支持 12/15/18/21/24")
    strength = mapping[num_words]
    return MNEMONIC_GEN.generate(strength=strength)


def _mnemonic_to_seed(mnemonic: str, passphrase: str = "") -> bytes:
    """通过 BIP39 标准将助记词转换为种子。"""
    if not MNEMONIC_GEN.check(mnemonic):
        raise ValueError("助记词校验未通过，请重试生成")
    return MNEMONIC_GEN.to_seed(mnemonic, passphrase)


def _derive_child(private_key: bytes, chain_code: bytes, index: int, hardened: bool) -> Tuple[bytes, bytes]:
    """执行单步 BIP32 子密钥派生。"""
    if hardened:
        data = b"\x00" + private_key + index.to_bytes(4, "big")
    else:
        pub_compressed = eth_keys.PrivateKey(private_key).public_key.to_compressed_bytes()
        data = pub_compressed + index.to_bytes(4, "big")
    I = hmac.new(chain_code, data, hashlib.sha512).digest()
    Il, Ir = I[:32], I[32:]
    child_int = (int.from_bytes(Il, "big") + int.from_bytes(private_key, "big")) % SECP256K1_N
    child_key = child_int.to_bytes(32, "big")
    return child_key, Ir


def _derive_private_key_from_path(seed: bytes, path: str) -> bytes:
    """从种子和路径计算最终私钥。"""
    I = hmac.new(b"Bitcoin seed", seed, hashlib.sha512).digest()
    priv, chain = I[:32], I[32:]
    segments = path.split("/")[1:]  # 跳过 m
    for seg in segments:
        hardened = seg.endswith("'")
        index = int(seg.rstrip("'"))
        if hardened:
            index += 0x80000000
        priv, chain = _derive_child(priv, chain, index, hardened)
    return priv


def _derive_account(mnemonic: str, path: str) -> Tuple[str, str]:
    """从助记词和派生路径生成地址与私钥。"""
    seed = _mnemonic_to_seed(mnemonic, "")
    priv_key_bytes = _derive_private_key_from_path(seed, path)
    acct = Account.from_key(priv_key_bytes)
    address = Web3.to_checksum_address(acct.address)
    private_key = acct.key.hex()
    return address, private_key


def generate_wallets(
    count: int,
    network_name: str,
    progress_cb: Optional[Callable[[int], None]] = None,
) -> List[WalletRecord]:
    """
    批量生成钱包记录（每个钱包独立助记词）。

    :param count: 生成数量
    :param network_name: 展示用的网络名称
    :param progress_cb: 进度回调，接受当前完成数量
    """
    wallets: List[WalletRecord] = []

    for i in range(count):
        mnemonic = _generate_mnemonic(12)
        path = DERIVATION_PATH_TEMPLATE.format(index=i)
        address, private_key = _derive_account(mnemonic, path)
        wallets.append(
            WalletRecord(
                index=i + 1,
                network=network_name,
                address=address,
                mnemonic=mnemonic,
                derivation_path=path,
                private_key=private_key,
            )
        )
        if progress_cb:
            progress_cb(i + 1)

    return wallets
