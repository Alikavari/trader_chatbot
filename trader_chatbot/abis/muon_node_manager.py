abi: list[dict] = [
    {
        "inputs": [
            {"internalType": "address", "name": "stakerAddress", "type": "address"}
        ],
        "name": "stakerAddressInfo",
        "outputs": [
            {
                "components": [
                    {"internalType": "uint64", "name": "id", "type": "uint64"},
                    {
                        "internalType": "address",
                        "name": "nodeAddress",
                        "type": "address",
                    },
                    {
                        "internalType": "address",
                        "name": "stakerAddress",
                        "type": "address",
                    },
                    {"internalType": "string", "name": "peerId", "type": "string"},
                    {"internalType": "bool", "name": "active", "type": "bool"},
                    {"internalType": "uint8", "name": "tier", "type": "uint8"},
                    {"internalType": "uint64[]", "name": "roles", "type": "uint64[]"},
                    {"internalType": "uint256", "name": "startTime", "type": "uint256"},
                    {"internalType": "uint256", "name": "endTime", "type": "uint256"},
                    {
                        "internalType": "uint256",
                        "name": "lastEditTime",
                        "type": "uint256",
                    },
                ],
                "internalType": "struct IMuonNodeManager.Node",
                "name": "node",
                "type": "tuple",
            },
        ],
        "stateMutability": "view",
        "type": "function",
    },
]
