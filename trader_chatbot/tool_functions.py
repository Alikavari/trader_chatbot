from langchain.tools import tool

from pydantic import BaseModel
from typing import Literal

from trader_chatbot.web3_read_functions import (
    getting_allowance,
    getting_balance,
    getting_node_info,
    getting_requsted_unstaked_amount,
    getting_claimable_time,
)

realTimeVariables = Literal[
    "stakedAmount",
    "nodePower",
    "rewardBalance",
    "balance",
    "requestedUnstakedAmount",
    "allownce",
]


@tool
async def get_variables(walletAddress: str, variableNames: list[realTimeVariables]):
    """
    Function for getting  realtime variables
    Args:
        walletAddress (str): User Ethereum wallet address begins with '0x' and is followed by 40 hexadecimal characters, consisting of digits (0–9) and letters (a–f).
        variableNames list[variableName] list of variables you need to their values
    Return:
        list[variableValue]
    """
    print("calling get_variables", "variableNames: ", variableNames)
    variables = []
    for variableName in variableNames:
        match variableName:
            case "stakedAmount":  # for getting stakedAmount
                print("\tcalling stakedAmount")
                out = await getting_node_info(walletAddress)
                variables.append(out["stakedAmount"])
            case "nodePower":  # for getting nodePower
                print("\tcalling nodePower")
                out = await getting_node_info(walletAddress)
                variables.append(out["nodePower"])
            case "rewardBalance":
                print("\tcalling reward")
                variables.append(100)
            case "balance":  # for gettting balance
                print("\tcalling balance")
                balance = await getting_balance(walletAddress)
                variables.append(balance)
            case "requestedUnstakedAmount":  # for getting requestedUnstakedAmount
                print("\tcalling requestedUnstakedAmount")
                requestedUnstakedAmount = getting_requsted_unstaked_amount(
                    walletAddress
                )
                variables.append(requestedUnstakedAmount)
            case "allownce":  # for getting allowance
                print("\tcalling allownce")
                allownce = getting_allowance(walletAddress)
                variables.append(allownce)
            case "tier":  # for getting tier
                print("\ncalling tier")
                out = await getting_node_info(walletAddress)
                variables.append(out["tier"])
    return variables


@tool
async def wellcome_message(
    walletAddress: str,
    user_UTC_hour_shift: int,
    user_UTC_min_shift: int,
    user_message_time_stamp: int,
):
    """
    A function to welcome and show some informatios to the user when user entered to chatbot .
    Args:
        walletAddress (str): User Ethereum wallet address begins with '0x' and is followed by 40 hexadecimal characters, consisting of digits (0–9) and letters (a–f).
        user_UTC_hour_shift (int): user local time hour
        user_UTC_min_shift (int): user local time min
        user_message_time_stamp (int): timestamp in the user message
    Returns:
        A string containing how the model should greet the user. (The audience for this report is you)
    """
    claiming_annoance = ""
    node_info = await getting_node_info(walletAddress)
    if node_info["pendingForClaim"] > 0:
        _, hr_claiming_time = getting_claimable_time(
            walletAddress, user_UTC_hour_shift, user_UTC_min_shift
        )
        claimable_time = getting_claimable_time(
            walletAddress, user_UTC_hour_shift, user_UTC_min_shift
        )[0]
        canClaimStake = user_message_time_stamp > claimable_time
        if canClaimStake == True:
            claiming_annoance = "The user can claim their unstaked assets right now"
        else:
            claiming_annoance = (
                "The user can claim their unstaked assets at" + hr_claiming_time
            )

    if node_info["nodeId"] == 0:
        return f"Event: The user connect its wallet right now, Thank the user sincerely for connecting the wallet . The user has not added a node yet. Guide the user if they want to add a node. the user balance is {node_info['balance']} show the balnce to user"

    return (
        f"Event: The user connect its wallet right now, Thank the user sincerely for connecting the wallet and show them these info in markdown table[parameters in left side of table and values in right side of table] (balance, nodepower,pending for claim and staked amount are in MUON$ and other paremeters doesnot have unit) {node_info}, "
        + claiming_annoance
    )


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
def get_claimable_epoch(
    walletAddress: str, user_UTC_hour_shift: int, user_UTC_min_shift: int
) -> tuple[int, str]:
    """
    Returns the claimable epoch time (in seconds) when a user can claim their unstaked amount.
    you should compare the  returned value of this function and timestamp flag of user message for underestanding that user can claim unstaked amount or not
    Args:
        walletAddress (str): User Ethereum wallet address begins with '0x' and is followed by 40 hexadecimal characters, consisting of digits (0–9) and letters (a–f).
        user_UTC_hour_shift (int): user local time hour
        user_UTC_min_shift (int): user local time min
    Returns tuple[int, str]:
        int: The epoch time in seconds when the user is eligible to claim their unstaked amount.
        str:Human-readable promised time for claiming (used to notify the user if the claiming time has not yet been reached)
    """
    claimable_unstake_time, hr_claimable_time = getting_claimable_time(
        walletAddress, user_UTC_hour_shift, user_UTC_min_shift
    )
    print("claimable_unstake_time: ", claimable_unstake_time)
    print("timezone: ", user_UTC_hour_shift, ":", user_UTC_min_shift)
    return claimable_unstake_time, hr_claimable_time


# ---------  write functions
@tool
def transfer(destinationWalletAddress: str, value: int):
    """
    This function is used for tranfering some muon coin to a wallet address t
    Args:
        destinationWalletAddress (str): an Ethereum wallet address begins with '0x' and is followed by 40 hexadecimal characters, consisting of digits (0–9) and letters (a–f).
        value: The amount that will be transfer (Important node: the transfer value should be equal or less than balnce before calling this function compare the transfer value and realtime balance)
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
def boost(amount):
    """
    increase the stakeamount of added node
    important note:
        Before performing a boost operation, first check the blance and allowance variables blance and allownce should be more than boost value, if allownce is not sufficient do approve user should know why approve is calling before boost
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
    claiming can be done when TIMESTAMP_FLAG was was more than claimabel epoch time
    Returns (str):
    the  transaction report
    """
    return "0"


@tool
def claim_reward():
    """
    claims reward (if availabe)
    fist check rewardBalance, if there is anything to claim, run this funcion.
    Returns (str):
    the  transaction report
    """
