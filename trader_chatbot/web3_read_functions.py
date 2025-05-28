from web3 import Web3
from trader_chatbot.abis.muon_node_staking import abi as node_staking_abi
from trader_chatbot.abis.muon_node_manager import abi as node_manager_abi
from trader_chatbot.abis.alice import abi as alice_abi
from typing import Any, Literal

from datetime import datetime, timedelta, timezone
import time
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

# Contract details
alice_contract_address = Web3.to_checksum_address(ALICE_CONTRACT_ADDRESS)
staking_contract_address = Web3.to_checksum_address(STAKING_CONTRACT_ADDRESS)
manager_contract_address = Web3.to_checksum_address(MANAGER_CONTRACT_ADDRESS)

# Connect to the Avalanche testnet RPC
rpc_url = RPC_URLS["avalanche-fuji"]

web3 = Web3(Web3.HTTPProvider(rpc_url))


def has_active_node(user_wallet_address: str) -> bool:
    contract = web3.eth.contract(address=manager_contract_address, abi=node_manager_abi)
    stakerAddressInfo = contract.functions.stakerAddressInfo(user_wallet_address)
    _, _, _, _, active, _, _, _, _, _ = stakerAddressInfo.call()
    return active


def has_node(user_wallet_address: str) -> bool:
    contract = web3.eth.contract(address=manager_contract_address, abi=node_manager_abi)
    stakerAddressInfo = contract.functions.stakerAddressInfo(user_wallet_address)
    _, _, _, _, _, _, _, _, _, nodeId = stakerAddressInfo.call()
    return nodeId


async def getting_node_info(user_wallet_address: str) -> dict[NodeInfoKeys, Any]:
    contract = web3.eth.contract(address=manager_contract_address, abi=node_manager_abi)
    stakerAddressInfo = contract.functions.stakerAddressInfo(user_wallet_address)
    id, stakerAddress, nodeAddress, peerID, active, tier, _, _, _, _ = (
        stakerAddressInfo.call()
    )

    contract = web3.eth.contract(address=staking_contract_address, abi=node_staking_abi)
    users = contract.functions.users(user_wallet_address)
    nodePower, _, _, _, tokenID = users.call()
    valueOfBondedToken = contract.functions.valueOfBondedToken(tokenID)
    stakedAmount = valueOfBondedToken.call()
    balance = await getting_balance(user_wallet_address)
    contract = web3.eth.contract(address=alice_contract_address, abi=alice_abi)
    decimals = contract.functions.decimals().call()
    decimalNodePower = from_bigint_to_decimal(nodePower, decimals)
    decimalStakeAmount = from_bigint_to_decimal(stakedAmount, decimals)
    decimalPnedingUnstakeAmount = getting_requsted_unstaked_amount(user_wallet_address)
    return {
        "stakerAddress": stakerAddress,
        "nodeAddress": nodeAddress,
        "peerID": peerID,
        "active": "Online" if active else "Offline",
        "tier": tier,
        "nodeId": id,
        "nodePower": decimalNodePower,
        "stakedAmount": decimalStakeAmount,
        "balance": f"{balance} MUON$",
        "pendingForClaimAmount": decimalPnedingUnstakeAmount,
    }


def getting_requsted_unstaked_amount(userWalletAddress: str):
    contract = web3.eth.contract(address=staking_contract_address, abi=node_staking_abi)
    # Call the `users` function
    row_rua = contract.functions.pendingUnstakes(userWalletAddress).call()
    contract = web3.eth.contract(address=alice_contract_address, abi=alice_abi)
    decimals = contract.functions.decimals().call()
    # Extract balance
    decimal_requested_unstaked_amount = from_bigint_to_decimal(row_rua, decimals)
    print("requsted_unstake: ", decimal_requested_unstaked_amount)
    return decimal_requested_unstaked_amount


def getting_allowance(ownerAddress: str):
    contract = web3.eth.contract(address=alice_contract_address, abi=alice_abi)
    # Call the `users` function
    raw_allowance = contract.functions.allowance(
        ownerAddress, staking_contract_address
    ).call()
    decimals = contract.functions.decimals().call()
    # Extract balance
    decimal_allowance = from_bigint_to_decimal(raw_allowance, decimals)
    return decimal_allowance


async def getting_balance(address: str) -> float:
    # Load the contract
    contract = web3.eth.contract(address=alice_contract_address, abi=alice_abi)
    # Call the `users` function
    raw_balance = contract.functions.balanceOf(address).call()
    decimals = contract.functions.decimals().call()
    # Extract balance
    decimal_balance = from_bigint_to_decimal(raw_balance, decimals)
    print("decimal_balance: ", decimal_balance)
    return decimal_balance


def show_time(time_reference, bias_hour, bias_min) -> str:
    # Get the current UTC time using time.time() and make it timezone-aware
    current_time_utc = datetime.fromtimestamp(time_reference, tz=timezone.utc)

    # Calculate the time difference (bias in hours and minutes)
    time_delta = timedelta(hours=bias_hour, minutes=bias_min)

    # Apply the time difference to the UTC time
    adjusted_time = current_time_utc + time_delta

    # Format the adjusted time to human-readable format
    human_readable_time = adjusted_time.strftime("%a %b %d %H:%M:%S %Y")

    return human_readable_time


def getting_claimable_time(
    address: str, user_UTC_hour_shift, user_UTC_min_shift
) -> tuple[int, str]:

    # Load the contract
    contract = web3.eth.contract(address=staking_contract_address, abi=node_staking_abi)
    # Call the `users` function
    exit_pending_period = contract.functions.exitPendingPeriod().call()
    # Load the contract
    contract = web3.eth.contract(address=staking_contract_address, abi=node_staking_abi)
    # Call the `users` function
    unstake_req_time = contract.functions.unstakeReqTimes(address).call()
    claimable_time: int = unstake_req_time + exit_pending_period
    hr_claimable_time = show_time(
        claimable_time, user_UTC_hour_shift, user_UTC_min_shift
    )
    return claimable_time, hr_claimable_time


def getting_reward_balance(address: str):
    contract = web3.eth.contract(address=staking_contract_address, abi=node_staking_abi)
    decimal_contract = web3.eth.contract(address=alice_contract_address, abi=alice_abi)
    raw_reward = contract.functions.earned(address).call()
    decimals = decimal_contract.functions.decimals().call()
    decimal_reward = from_bigint_to_decimal(raw_reward, decimals)
    print("decimal_reward: ", decimal_reward)
    return decimal_reward
