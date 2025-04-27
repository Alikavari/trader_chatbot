from typing import Literal

RpcNames = Literal["avalanche-fuji"]
RPC_URLS: dict[RpcNames, str] = {
    "avalanche-fuji": "https://avalanche-fuji-c-chain-rpc.publicnode.com"
}

ALICE_CONTRACT_ADDRESS = "0x383FA34836A5F5D3805e77df4f60A62D75034579"

PROMPT_DIR = "./prompts/prompt.txt"
