from langchain.tools import tool

from pydantic import BaseModel
from typing import Literal
from typing import Annotated
import time
from trader_chatbot.web3_read_functions import (
    getting_allowance,
    getting_balance,
    getting_node_info,
    getting_requsted_unstaked_amount,
    getting_claimable_time,
    getting_reward_balance,
    has_node,
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
async def handle_wallet_connect(
    userWalletAddress: str,
    user_UTC_hour_shift: int,
    user_UTC_min_shift: int,
):
    "This function is run when user connect its wallet address"
    print("calling handle wallet connection event")
    node_info = await getting_node_info(userWalletAddress)
    if node_info["nodeId"] == 0:
        return f"Event: The user connect its wallet right now, Thank the user sincerely for connecting the wallet . The user has not added a node yet. Guide the user if they want to add a node. the user balance is {node_info['balance']} show the balnce to user"
    print(f"\n\n{node_info}")

    climable_time = await hr_climble_time(
        userWalletAddress, user_UTC_hour_shift, user_UTC_min_shift
    )
    print("climableTime:", climable_time)
    return (
        f"Thank user for connecting wallet; display {node_info.keys()} {node_info} parameters in a markdown table \n "
        + climable_time
    )


@tool
async def get_variables(
    userWalletAddress: Annotated[str, "User Ethereum wallet address"],
    variableNames: Annotated[list[str], "List required variable names"],
    user_UTC_hour_shift: int,
    user_UTC_min_shift: int,
):
    """
    Function for getting MUON variables
    """
    print("calling get_variables", "variableNames: ", variableNames)
    variables = []
    out = await getting_node_info(userWalletAddress)
    for variableName in variableNames:
        match variableName:
            case "stakedAmount":  # for getting stakedAmount
                print("\tcalling stakedAmount")
                variables.append(out["stakedAmount"])
            case "nodePower":  # for getting nodePower
                print("\tcalling nodePower")
                variables.append(out["nodePower"])
            case "nodeID":
                variables.append(out["nodeId"])
            case "nodeAddress":
                variables.append(out["nodeAddress"])
            case "rewardBalance":
                print("\tcalling reward")
                reward_balance = getting_reward_balance(userWalletAddress)
                variables.append(reward_balance)
            case "balance":  # for gettting balance
                print("\tcalling balance")
                balance = await getting_balance(userWalletAddress)
                print("balance: ", balance)
                variables.append(balance)
            case "unstakeBalance":  # for getting requestedUnstakedAmount
                print("\tcalling unstakeBalance")
                unstakeBalance = getting_requsted_unstaked_amount(userWalletAddress)
                variables.append(unstakeBalance)
            case "allownce":  # for getting allowance
                print("\tcalling allownce")
                allownce = getting_allowance(userWalletAddress)
                variables.append(allownce)
            case "nodeStatus":
                print("\tcalling nodeStatus")
                variables.append(out["active"])
            case "tier":
                print("\t calling tier")
                variables.append(out["tier"])
            case "peerID":
                print("\r calling peerID")
                variables.append(out["peerID"])
    return variables


async def hr_climble_time(
    userWalletAddress: str, user_UTC_hour_shift: int, user_UTC_min_shift: int
):
    unstakeBalance = getting_requsted_unstaked_amount(userWalletAddress)
    if unstakeBalance <= 0:
        return "nothing available to claim"

    current_epoch = int(time.time())
    claimable_time, hr_claimable_time = getting_claimable_time(
        userWalletAddress, user_UTC_hour_shift, user_UTC_min_shift
    )
    if current_epoch >= claimable_time:
        return (
            # f"you cannot get your claim balacen right now, try agian in {hr_claimable_time}",
            "User can get their unstake balance right now"
        )
    else:
        return "User can get their unstake balance on {user_UTC_min_shift}"


@tool
async def climable_time(
    userWalletAddress: str, user_UTC_hour_shift: int, user_UTC_min_shift: int
):
    """fuction for getting climalbe time"""
    print("calling climable_time")
    unstakeBalance = getting_requsted_unstaked_amount(userWalletAddress)
    if unstakeBalance <= 0:
        return "nothing available to claim"

    current_epoch = int(time.time())
    claimable_time, hr_claimable_time = getting_claimable_time(
        userWalletAddress, user_UTC_hour_shift, user_UTC_min_shift
    )
    if current_epoch >= claimable_time:
        return (
            # f"you cannot get your claim balacen right now, try agian in {hr_claimable_time}",
            "User can get your unstake balance right now"
        )
    else:
        return "User can  get your unstake balance on {user_UTC_min_shift}"


# ---------  write functions
@tool
async def transfer(userWalletAddress: str, destinationWalletAddress: str, amount: int):
    """
    Function transfers MUON coins to a wallet address
    """
    print("calling transfer")
    balance = await getting_balance(userWalletAddress)
    if amount > balance:
        return "Transfer failed due to insufficient balance", False
    return "success", True


@tool
async def boost(userWalletAddress: str, amount: int):
    """boosting some amount to node"""
    # return f"boosting failed due to insufficient allowacne first auto-run  the approve {amount} without user permission then call boost"
    print("calling boost")
    allownce = getting_allowance(userWalletAddress)
    balance = await getting_balance(userWalletAddress)
    print("balance:", balance)
    print("amount: ", amount)
    if amount > balance:
        return "boosting failed due to insufficient balance", False
    if amount > allownce:
        return (
            f"Boosting failed due to low allowance run approve({amount}) with no user confirmation. Explain why approval is needed before boosting.",
            False,
        )

    return "boosting done success", True


@tool
async def approve(userWalletAddress: str, amount: int):
    """
    approves MUON coins for a spender
    """
    print("calling approve")
    balance = await getting_balance(userWalletAddress)
    print("balance:", balance)
    if amount > balance:
        return "approving failed due to insufficient balance", False
    return "success", True


@tool
async def chek_for_adding_node(userWalletAddress: str):
    """should run before adding node"""
    if has_node(userWalletAddress) != 0:
        return "Adding node failed—node already set up, cannot add again."


@tool
async def add_node(
    userWalletAddress: str, nodeIp: str, nodeAddress: str, peerID: str, amount: int
):
    """
    This function add a node on muon chian
    """
    balance = await getting_balance(userWalletAddress)
    if amount > balance:
        return "Adding node failed due to insufficient balance", False

    allownce = getting_allowance(userWalletAddress)
    if amount > allownce:
        return (
            f"Adding node failed due to low allowance first run approve({amount}) with no user confirmation. Explain why approval is needed before boosting. then boost",
            False,
        )

    return "", True


@tool
async def unstake(userWalletAddress: str, amount: int):
    """
    This function unstakes some muon coin from node
    """
    print("calling unstake")
    out = await getting_node_info(userWalletAddress)
    if amount > out["stakedAmount"]:
        return "Unstake failed—amount must be less than staked amount", False
    return "success", True


@tool
def claim(userWalletAddress: str, user_UTC_hour_shift: int, user_UTC_min_shift: int):
    """
    claims unstake balance
    """
    print("calling claim")
    unstakeBalance = getting_requsted_unstaked_amount(userWalletAddress)
    print(unstakeBalance)
    if unstakeBalance <= 0:
        print("the if condition is runed")
        return "Operation failed—nothing available to claim", False
    claimable_time, hr_claimable_time = getting_claimable_time(
        userWalletAddress, user_UTC_hour_shift, user_UTC_min_shift
    )
    current_epoch = int(time.time())
    if current_epoch < claimable_time:
        return (
            f"you cannot get your claim balacen right now, try agian in {hr_claimable_time}",
            False,
        )
    return "success", True


@tool
def claim_reward(userWalletAddress: str):
    """
    claims reward
    """
    print("calling claiming reward")
    rewardBalance = getting_reward_balance(userWalletAddress)
    if rewardBalance <= 0:
        return "Operation failed, no reward to claim.", False
    return "success", True
