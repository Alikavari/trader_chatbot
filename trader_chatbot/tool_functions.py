from web3 import Web3
from datetime import datetime, timezone

from eth_typing import Address
from trader_chatbot.toolkits.web3_convertion import from_bigint_to_decimal
from trader_chatbot.constants import (
    RPC_URLS,
    ALICE_CONTRACT_ADDRESS,
    STAKING_CONTRACT_ADDRESS,
    MANAGER_CONTRACT_ADDRESS,
)
from langchain.tools import tool
from trader_chatbot.abis.muon_node_staking import abi as node_staking_abi
from trader_chatbot.abis.muon_node_manager import abi as node_manager_abi
from trader_chatbot.abis.alice import abi as alice_abi

from pydantic import BaseModel


# Connect to the Avalanche testnet RPC
rpc_url = RPC_URLS["avalanche-fuji"]

web3 = Web3(Web3.HTTPProvider(rpc_url))


# Contract details
alice_contract_address = Web3.to_checksum_address(ALICE_CONTRACT_ADDRESS)
staking_contract_address = Web3.to_checksum_address(STAKING_CONTRACT_ADDRESS)
manager_contract_address = Web3.to_checksum_address(MANAGER_CONTRACT_ADDRESS)


async def getting_node_info(user_wallet_address: str):
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
    balance = await getting_balance_web3(user_wallet_address)
    contract = web3.eth.contract(address=alice_contract_address, abi=alice_abi)
    decimals = contract.functions.decimals().call()
    decimalNodePower = from_bigint_to_decimal(nodePower, decimals)
    decimalStakeAmount = from_bigint_to_decimal(stakedAmount, decimals)
    print("calling nodeInfo")
    return {
        "id": id,
        "stakerAddress": stakerAddress,
        "nodeAddress": nodeAddress,
        "peerID": peerID,
        "active": active,
        "tier": tier,
        "nodePower": decimalNodePower,
        "stakedAmount": decimalStakeAmount,
        "balance": balance,
    }


async def getting_balance_web3(address: str) -> int:
    # Load the contract
    contract = web3.eth.contract(address=alice_contract_address, abi=alice_abi)
    # Call the `users` function
    raw_balance = contract.functions.balanceOf(address).call()
    decimals = contract.functions.decimals().call()
    # Extract balance
    decimal_balance = from_bigint_to_decimal(raw_balance, decimals)
    print("decimal_balance: ", decimal_balance)
    return decimal_balance


@tool
async def get_balance(walletAddress: str):
    """
    Function for getting user balnce.
    Args:
        walletAddress (str): User Ethereum wallet address begins with '0x' and is followed by 40 hexadecimal characters, consisting of digits (0–9) and letters (a–f).
    Returns:
        user balance in muon$ (int)
    """
    decimal_balance = await getting_balance_web3(walletAddress)

    return decimal_balance


@tool
async def wellcome_message(walletAddress: str):
    """
    A function to welcome and show some informatios to the user when user entered to chatbot .
    Args:
        walletAddress (str): User Ethereum wallet address begins with '0x' and is followed by 40 hexadecimal characters, consisting of digits (0–9) and letters (a–f).
    Returns:
        A string containing how the model should greet the user. (The audience for this report is you)
    """
    node_info = await getting_node_info(walletAddress)
    if node_info["id"] == 0:
        return f"Event: The user connect its wallet right now, Thank the user sincerely for connecting the wallet . The user has not added a node yet. Guide the user if they want to add a node. the user balance is {node_info['balance']} show the balnce to user "

    return f"Event: The user connect its wallet right now, Thank the user sincerely for connecting the wallet and show them these info in markdown table[parameters in left side of table and values in right side of table] (nodepower and staked amount are in muon$ and other paremeters doesnot have unit) {node_info}"


@tool
async def node_info(walletAddress: str):
    """
    This function should be call when user wants to see their node_status/node_info
    Args:
        walletAddress (str): User Ethereum wallet address begins with '0x' and is followed by 40 hexadecimal characters, consisting of digits (0–9) and letters (a–f).
    Returns:
        node status report (str)
    """
    node_info = await getting_node_info(walletAddress)
    return f"the user node info is {node_info} show it in markdown tabel to user"


@tool
async def get_staked_amount(walletAddress: str):
    """
    you can get realtime staked_amount parameter value form this function
    Args:
        walletAddress (str): User Ethereum wallet address begins with '0x' and is followed by 40 hexadecimal characters, consisting of digits (0–9) and letters (a–f).
    Returns:
        (int) stakedamount value
    """
    print("calling unstake amount")
    node_info = await getting_node_info(walletAddress)
    return node_info["stakedAmount"]


@tool
def transfer(destinationWalletAddress: str, value: int):
    """
    This function is used for tranfering some muon coin to a wallet address
    Args:
        destinationWalletAddress (str): an Ethereum wallet address begins with '0x' and is followed by 40 hexadecimal characters, consisting of digits (0–9) and letters (a–f).
        value: The amount that will be transfer
    Retruns (str):
        The transfer report in (str)
    """

    return "success"


@tool
def approve(value: int):
    """
    This function is used for approving some muon coin to a spender. (this function calls a web3 transaction )

    Args:
        value: The amount value that will be approve (Replaced with current allowance amount, not cumulative.)
    Retruns (str):
        The transaction report in (str)
    """
    return "success"


@tool
def add_node(nodeIp: str, nodeAddress: str, peerID: str, amount: int):
    """
    This function add a node on muon chian (Important: adding node needs allowance check and balance check both allowance and balance should be equal or more than stakeamount of adding node if balnce is insufficent user should buy coin if allowance is not sufficient approve appropriate coin for user   )
    Arge:
        nodeIP (str): The Ip of node
        nodeAddress (str) The nodeWalletAddress,
        peerId (str): libp2p peerID format (warm the user if the entered peerID by user did not follow correct format)
        amout (int): the stakeamount (this field should be more than 500, if user ented value less than 500 you should warn the user to enter valid amount)
    Returns (str):
        The transaction report in (str)
    """
    return "success"


@tool
def unstake(amount: int):
    """
    This function unstakes some muon coin from node (fist check staked amount [dont rely the staked amount on chathistory check it from get_staked_amount funciton everytime you are calling unstake]. the amount user wants to unstake should be less or equal than stakedamount variable)
    Arge:
        amount (int): the value that user wants to unstake
    Returns (str):
        The transaction report in (str)
    """
    return "success"


@tool
def allowance(ownerAddress):
    """
    checks how much muon owner  approved for spender
    Args:
        ownerAddress (str): its user wallet address
        spenderAddress (str): the spender address. (it starts with 0x)
    Returns (str):
        the  transaction report contains allownce in muon$
    """
    contract = web3.eth.contract(address=alice_contract_address, abi=alice_abi)
    # Call the `users` function
    raw_allowance = contract.functions.allowance(
        ownerAddress, staking_contract_address
    ).call()
    decimals = contract.functions.decimals().call()
    # Extract balance
    decimal_allowance = from_bigint_to_decimal(raw_allowance, decimals)
    print("calling allowance")
    return f"decimal_allowance: {decimal_allowance}"


@tool
def boost(amount):
    """
    increase the stakeamount of added node (important note: for boosting first check the balnce the balnce should be equal or more than boost value, dont call boost if balnce is insufficient. after that, check allowance, if allowance is less than boost value, call approve fist and explain[while calling approve] to user why approvemnet is needed)
    Args:
        amount (int): the boost amount (in MUON $)
    Returns (str):
    the  transaction report
    """
    return "0"


@tool
def claim():
    """
    claims requested unstaked amount for calling this funciton reuqsted_unstaked_amount should be more than 0 (dont run it if requested_unstaked_amount is 0)
    check time by calling getting time
    Returns (str):
    the  transaction report
    """
    return "0"


@tool
def getting_time():
    """
    function for getting utc time (clock)
    if user want about time you can call this functio, this function give you utc time
    Returns:
        string contains utc time
    """
    # Get current UTC time
    utc_time = datetime.now(timezone.utc)

    # Print it in ISO format
    return f"UTC Time: {utc_time.isoformat()}"


@tool
def getting_requsted_unstaked_amount(userWalletAddress: str):
    """
    function for getting requested unstaked amount variable.
    Args:
        userWalletAddress:
    Returns:
     requested unstaked amount (int)
    """
    contract = web3.eth.contract(address=staking_contract_address, abi=node_staking_abi)
    # Call the `users` function
    row_rua = contract.functions.pendingUnstakes(userWalletAddress).call()
    contract = web3.eth.contract(address=alice_contract_address, abi=alice_abi)
    decimals = contract.functions.decimals().call()
    # Extract balance
    decimal_requested_unstaked_amount = from_bigint_to_decimal(row_rua, decimals)
    print("requsted_unstake: ", decimal_requested_unstaked_amount)
    return decimal_requested_unstaked_amount
