from web3 import Web3
from eth_typing import Address
from trader_chatbot.abi_list import abi
from trader_chatbot.toolkits.web3_convertion import from_bigint_to_decimal
from trader_chatbot.constants import RPC_URLS, ALICE_CONTRACT_ADDRESS
from langchain.tools import tool

# Connect to the Avalanche testnet RPC
rpc_url = RPC_URLS["avalanche-fuji"]

web3 = Web3(Web3.HTTPProvider(rpc_url))


# Contract details
contract_address = Web3.to_checksum_address(ALICE_CONTRACT_ADDRESS)


async def getting_balance_web3(address: str) -> int:
    # Load the contract
    contract = web3.eth.contract(address=contract_address, abi=abi)
    # Call the `users` function
    raw_balance = contract.functions.balanceOf(address).call()
    decimals = contract.functions.decimals().call()
    # Extract balance
    decimal_balance = from_bigint_to_decimal(raw_balance, decimals)
    print("decimal_balance: ", decimal_balance)
    return decimal_balance


@tool
async def get_balance(address: str):
    """
    Function for getting user balnce .
    Args:
        address (str): an Ethereum address starts with 0x
    Returns:
        user balance in muon$
    """
    decimal_balance = await getting_balance_web3(address)

    return decimal_balance


@tool
async def wellcome_message(address: str):
    """
    A function to welcome and show some informatios to the user when user entered to chatbot .
    Args:
        address (str): an Ethereum address starts with 0x
    Returns:
        A string containing how the model should greet the user.
    """
    value = await getting_balance_web3(address)
    return f"Event: The user connect its wallet right now, Thank the user sincerely for connecting the wallet and tell them how much balance they have. the  user balance is {value} Muon$"


@tool
def transfer(destination_wallet_address: str, value: int):
    """
    This function is used for tranfering some coin to a wallet address
    Args:
        destination_wallet_address (str): the destination wallet address starts with 0x
        value: The amount value that will be transfer
    Retruns:
        True (success) or False (Failed)
    """

    return True


# def get_user_info(address: str):
#     """
#     Function for getting user info.
#     Input parameters:
#         address (str): an Ethereum address starts with 0x
#     Returns:
#         a dict with these keys(balance, paidReward, paidRewardPerToken, pendingRewards, tokenId)
#     """

#     # Load the contract
#     contract = web3.eth.contract(address=contract_address, abi=abi)
#     # Call the `users` function
#     user_data = contract.functions.users(address).call()
#     # Extract balance
#     return {
#         "balance": user_data[0],
#         "paidReward": user_data[1],
#         "paidRewardPerToken": user_data[2],
#         "pendingRewards": user_data[3],
#         "tokenId": user_data[4],
#     }


# @tool
# def network_status():
#     pass


# @tool
# def add_node():
#     pass


# @tool
# async def check_network_status():
#     """
#     This function is used for checking the network status
#     input: NULL
#     return a number between 0-9 (0bad and 9 is perfect)
#     """
#     return 0
