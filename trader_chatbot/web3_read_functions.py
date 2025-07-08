from web3 import AsyncWeb3, AsyncHTTPProvider
from trader_chatbot.abis.muon_node_staking import abi as node_staking_abi
from trader_chatbot.abis.muon_node_manager import abi as node_manager_abi
from trader_chatbot.abis.alice import abi as alice_abi
from typing import Any, Literal, cast
from dotenv import load_dotenv
import os
from datetime import datetime, timedelta, timezone
from trader_chatbot.toolkits.web3_convertion import from_bigint_to_decimal
from trader_chatbot.constants import (
    RPC_URLS,
    ALICE_CONTRACT_ADDRESS,
    STAKING_CONTRACT_ADDRESS,
    MANAGER_CONTRACT_ADDRESS,
)

NodeInfoKeys = Literal[
    "stakerAddress",
    "nodeAddress",
    "peerID",
    "active",
    "tier",
    "nodeId",
    "nodePower",
    "stakedAmount",
    "balance",
    "pendingForClaimAmount",
]

load_dotenv()
chain_id = cast(str, os.getenv("CHAIN_ID"))

print("the chain id: ", chain_id)

# Contract addresses
alice_contract_address = AsyncWeb3.to_checksum_address(ALICE_CONTRACT_ADDRESS[chain_id])
staking_contract_address = AsyncWeb3.to_checksum_address(
    STAKING_CONTRACT_ADDRESS[chain_id]
)
manager_contract_address = AsyncWeb3.to_checksum_address(
    MANAGER_CONTRACT_ADDRESS[chain_id]
)

# Connect to the RPC
rpc_url = RPC_URLS[chain_id]
web3 = AsyncWeb3(AsyncHTTPProvider(rpc_url))


async def has_active_node(user_wallet_address: str) -> bool:
    contract = web3.eth.contract(address=manager_contract_address, abi=node_manager_abi)
    stakerAddressInfo = contract.functions.stakerAddressInfo(user_wallet_address)
    _, _, _, _, active, _, _, _, _, _ = await stakerAddressInfo.call()
    return active


async def has_node(user_wallet_address: str) -> bool:
    contract = web3.eth.contract(address=manager_contract_address, abi=node_manager_abi)
    stakerAddressInfo = contract.functions.stakerAddressInfo(user_wallet_address)
    _, _, _, _, _, _, _, _, _, nodeId = await stakerAddressInfo.call()
    return nodeId


async def getting_node_info(user_wallet_address: str) -> dict[NodeInfoKeys, Any]:
    contract = web3.eth.contract(address=manager_contract_address, abi=node_manager_abi)
    stakerAddressInfo = contract.functions.stakerAddressInfo(user_wallet_address)
    id, stakerAddress, nodeAddress, peerID, active, tier, _, _, _, _ = (
        await stakerAddressInfo.call()
    )

    contract = web3.eth.contract(address=staking_contract_address, abi=node_staking_abi)
    users = contract.functions.users(user_wallet_address)
    nodePower, _, _, _, tokenID = await users.call()

    valueOfBondedToken = contract.functions.valueOfBondedToken(tokenID)
    stakedAmount = await valueOfBondedToken.call()

    balance = await getting_balance(user_wallet_address)

    contract = web3.eth.contract(address=alice_contract_address, abi=alice_abi)
    decimals = await contract.functions.decimals().call()

    decimalNodePower = from_bigint_to_decimal(nodePower, decimals)
    decimalStakeAmount = from_bigint_to_decimal(stakedAmount, decimals)
    decimalPendingUnstakeAmount = await getting_requsted_unstaked_amount(
        user_wallet_address
    )

    return {
        "stakerAddress": stakerAddress,
        "nodeAddress": nodeAddress,
        "peerID": peerID,
        "active": "Online" if active else "Offline",
        "tier": tier,
        "nodeId": id,
        "nodePower": decimalNodePower,
        "stakedAmount": decimalStakeAmount,
        "balance": f"{balance} $MUON",
        "pendingForClaimAmount": decimalPendingUnstakeAmount,
    }


async def getting_requsted_unstaked_amount(userWalletAddress: str):
    contract = web3.eth.contract(address=staking_contract_address, abi=node_staking_abi)
    row_rua = await contract.functions.pendingUnstakes(userWalletAddress).call()

    contract = web3.eth.contract(address=alice_contract_address, abi=alice_abi)
    decimals = await contract.functions.decimals().call()

    decimal_requested_unstaked_amount = from_bigint_to_decimal(row_rua, decimals)
    print("requsted_unstake: ", decimal_requested_unstaked_amount)
    return decimal_requested_unstaked_amount


async def getting_allowance(ownerAddress: str):
    contract = web3.eth.contract(address=alice_contract_address, abi=alice_abi)
    raw_allowance = await contract.functions.allowance(
        ownerAddress, staking_contract_address
    ).call()
    decimals = await contract.functions.decimals().call()
    decimal_allowance = from_bigint_to_decimal(raw_allowance, decimals)
    return decimal_allowance


async def getting_balance(address: str) -> float:
    contract = web3.eth.contract(address=alice_contract_address, abi=alice_abi)
    raw_balance = await contract.functions.balanceOf(address).call()
    decimals = await contract.functions.decimals().call()
    decimal_balance = from_bigint_to_decimal(raw_balance, decimals)
    print("decimal_balance: ", decimal_balance)
    print("the chain id: ", chain_id)
    return decimal_balance


def show_time(time_reference, bias_hour, bias_min) -> str:
    current_time_utc = datetime.fromtimestamp(time_reference, tz=timezone.utc)
    time_delta = timedelta(hours=bias_hour, minutes=bias_min)
    adjusted_time = current_time_utc + time_delta
    human_readable_time = adjusted_time.strftime("%a %b %d %H:%M:%S %Y")
    return human_readable_time


async def getting_claimable_time(
    address: str, user_UTC_hour_shift, user_UTC_min_shift
) -> tuple[int, str]:
    contract = web3.eth.contract(address=staking_contract_address, abi=node_staking_abi)
    exit_pending_period = await contract.functions.exitPendingPeriod().call()
    unstake_req_time = await contract.functions.unstakeReqTimes(address).call()

    claimable_time: int = unstake_req_time + exit_pending_period
    hr_claimable_time = show_time(
        claimable_time, user_UTC_hour_shift, user_UTC_min_shift
    )
    return claimable_time, hr_claimable_time


async def getting_reward_balance(address: str):
    contract = web3.eth.contract(address=staking_contract_address, abi=node_staking_abi)
    decimal_contract = web3.eth.contract(address=alice_contract_address, abi=alice_abi)
    raw_reward = await contract.functions.earned(address).call()
    decimals = await decimal_contract.functions.decimals().call()
    decimal_reward = from_bigint_to_decimal(raw_reward, decimals)
    print("decimal_reward: ", decimal_reward)
    return decimal_reward
