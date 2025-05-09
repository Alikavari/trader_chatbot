from typing import Literal

RpcNames = Literal["avalanche-fuji"]
RPC_URLS: dict[RpcNames, str] = {
    "avalanche-fuji": "https://avalanche-fuji-c-chain-rpc.publicnode.com"
}

ALICE_CONTRACT_ADDRESS = "0x383FA34836A5F5D3805e77df4f60A62D75034579"
STAKING_CONTRACT_ADDRESS = "0xcB6F8f4eaA80148d16D08543b84770d71d7Bcd7f"
MANAGER_CONTRACT_ADDRESS = "0x4b41C5D49Cdd992E7C6b07225731d72233E1ef64"
PROMPT_DIR = "./prompts/prompt.txt"
