DIVA_ABI = [
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "address", "name": "from", "type": "address"},
            {"indexed": True, "internalType": "address", "name": "to", "type": "address"},
            {"indexed": True, "internalType": "address", "name": "collateralToken", "type": "address"},
            {"indexed": False, "internalType": "uint256", "name": "amount", "type": "uint256"},
        ],
        "name": "FeeClaimTransferred",
        "type": "event",
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "address", "name": "by", "type": "address"},
            {"indexed": True, "internalType": "address", "name": "collateralToken", "type": "address"},
            {"indexed": False, "internalType": "uint256", "name": "amount", "type": "uint256"},
        ],
        "name": "FeesClaimed",
        "type": "event",
    },
    {
        "inputs": [{"internalType": "address", "name": "_collateralToken", "type": "address"}],
        "name": "claimFees",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [
            {"internalType": "address", "name": "_recipient", "type": "address"},
            {"internalType": "address", "name": "_collateralToken", "type": "address"},
            {"internalType": "uint256", "name": "_amount", "type": "uint256"},
        ],
        "name": "transferFeeClaim",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "anonymous": False,
        "inputs": [
            {
                "components": [
                    {"internalType": "address", "name": "facetAddress", "type": "address"},
                    {"internalType": "enum IDiamondCut.FacetCutAction", "name": "action", "type": "uint8"},
                    {"internalType": "bytes4[]", "name": "functionSelectors", "type": "bytes4[]"},
                ],
                "indexed": False,
                "internalType": "struct IDiamondCut.FacetCut[]",
                "name": "_diamondCut",
                "type": "tuple[]",
            },
            {"indexed": False, "internalType": "address", "name": "_init", "type": "address"},
            {"indexed": False, "internalType": "bytes", "name": "_calldata", "type": "bytes"},
        ],
        "name": "DiamondCut",
        "type": "event",
    },
    {
        "inputs": [
            {
                "components": [
                    {"internalType": "address", "name": "facetAddress", "type": "address"},
                    {"internalType": "enum IDiamondCut.FacetCutAction", "name": "action", "type": "uint8"},
                    {"internalType": "bytes4[]", "name": "functionSelectors", "type": "bytes4[]"},
                ],
                "internalType": "struct IDiamondCut.FacetCut[]",
                "name": "_diamondCut",
                "type": "tuple[]",
            },
            {"internalType": "address", "name": "_init", "type": "address"},
            {"internalType": "bytes", "name": "_calldata", "type": "bytes"},
        ],
        "name": "diamondCut",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [{"internalType": "bytes4", "name": "_functionSelector", "type": "bytes4"}],
        "name": "facetAddress",
        "outputs": [{"internalType": "address", "name": "facetAddress_", "type": "address"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "facetAddresses",
        "outputs": [{"internalType": "address[]", "name": "facetAddresses_", "type": "address[]"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [{"internalType": "address", "name": "_facet", "type": "address"}],
        "name": "facetFunctionSelectors",
        "outputs": [{"internalType": "bytes4[]", "name": "facetFunctionSelectors_", "type": "bytes4[]"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "facets",
        "outputs": [
            {
                "components": [
                    {"internalType": "address", "name": "facetAddress", "type": "address"},
                    {"internalType": "bytes4[]", "name": "functionSelectors", "type": "bytes4[]"},
                ],
                "internalType": "struct IDiamondLoupe.Facet[]",
                "name": "facets_",
                "type": "tuple[]",
            }
        ],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [{"internalType": "bytes4", "name": "_interfaceId", "type": "bytes4"}],
        "name": "supportsInterface",
        "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [
            {"internalType": "address", "name": "_collateralToken", "type": "address"},
            {"internalType": "address", "name": "_recipient", "type": "address"},
        ],
        "name": "getClaims",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "getGovernanceParameters",
        "outputs": [
            {
                "components": [
                    {"internalType": "uint256", "name": "submissionPeriod", "type": "uint256"},
                    {"internalType": "uint256", "name": "challengePeriod", "type": "uint256"},
                    {"internalType": "uint256", "name": "reviewPeriod", "type": "uint256"},
                    {"internalType": "uint256", "name": "fallbackSubmissionPeriod", "type": "uint256"},
                    {"internalType": "address", "name": "treasury", "type": "address"},
                    {"internalType": "address", "name": "fallbackDataProvider", "type": "address"},
                    {"internalType": "uint256", "name": "pauseReturnCollateralUntil", "type": "uint256"},
                    {"internalType": "uint96", "name": "protocolFee", "type": "uint96"},
                    {"internalType": "uint96", "name": "settlementFee", "type": "uint96"},
                ],
                "internalType": "struct LibDiamond.GovernanceStorage",
                "name": "",
                "type": "tuple",
            }
        ],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "getLatestPoolId",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [{"internalType": "bytes32", "name": "_poolId", "type": "bytes32"}],
        "name": "getPoolParameters",
        "outputs": [
            {
                "components": [
                    {"internalType": "uint256", "name": "floor", "type": "uint256"},
                    {"internalType": "uint256", "name": "inflection", "type": "uint256"},
                    {"internalType": "uint256", "name": "cap", "type": "uint256"},
                    {"internalType": "uint256", "name": "gradient", "type": "uint256"},
                    {"internalType": "uint256", "name": "collateralBalance", "type": "uint256"},
                    {"internalType": "uint256", "name": "finalReferenceValue", "type": "uint256"},
                    {"internalType": "uint256", "name": "capacity", "type": "uint256"},
                    {"internalType": "uint256", "name": "statusTimestamp", "type": "uint256"},
                    {"internalType": "address", "name": "shortToken", "type": "address"},
                    {"internalType": "uint96", "name": "payoutShort", "type": "uint96"},
                    {"internalType": "address", "name": "longToken", "type": "address"},
                    {"internalType": "uint96", "name": "payoutLong", "type": "uint96"},
                    {"internalType": "address", "name": "collateralToken", "type": "address"},
                    {"internalType": "uint96", "name": "expiryTime", "type": "uint96"},
                    {"internalType": "address", "name": "dataProvider", "type": "address"},
                    {"internalType": "uint96", "name": "protocolFee", "type": "uint96"},
                    {"internalType": "uint96", "name": "settlementFee", "type": "uint96"},
                    {"internalType": "enum LibDiamond.Status", "name": "statusFinalReferenceValue", "type": "uint8"},
                    {"internalType": "string", "name": "referenceAsset", "type": "string"},
                ],
                "internalType": "struct LibDiamond.Pool",
                "name": "",
                "type": "tuple",
            }
        ],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [{"internalType": "address", "name": "_positionToken", "type": "address"}],
        "name": "getPoolParametersByAddress",
        "outputs": [
            {
                "components": [
                    {"internalType": "uint256", "name": "floor", "type": "uint256"},
                    {"internalType": "uint256", "name": "inflection", "type": "uint256"},
                    {"internalType": "uint256", "name": "cap", "type": "uint256"},
                    {"internalType": "uint256", "name": "gradient", "type": "uint256"},
                    {"internalType": "uint256", "name": "collateralBalance", "type": "uint256"},
                    {"internalType": "uint256", "name": "finalReferenceValue", "type": "uint256"},
                    {"internalType": "uint256", "name": "capacity", "type": "uint256"},
                    {"internalType": "uint256", "name": "statusTimestamp", "type": "uint256"},
                    {"internalType": "address", "name": "shortToken", "type": "address"},
                    {"internalType": "uint96", "name": "payoutShort", "type": "uint96"},
                    {"internalType": "address", "name": "longToken", "type": "address"},
                    {"internalType": "uint96", "name": "payoutLong", "type": "uint96"},
                    {"internalType": "address", "name": "collateralToken", "type": "address"},
                    {"internalType": "uint96", "name": "expiryTime", "type": "uint96"},
                    {"internalType": "address", "name": "dataProvider", "type": "address"},
                    {"internalType": "uint96", "name": "protocolFee", "type": "uint96"},
                    {"internalType": "uint96", "name": "settlementFee", "type": "uint96"},
                    {"internalType": "enum LibDiamond.Status", "name": "statusFinalReferenceValue", "type": "uint8"},
                    {"internalType": "string", "name": "referenceAsset", "type": "string"},
                ],
                "internalType": "struct LibDiamond.Pool",
                "name": "",
                "type": "tuple",
            }
        ],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "address", "name": "from", "type": "address"},
            {"indexed": False, "internalType": "uint256", "name": "period", "type": "uint256"},
        ],
        "name": "ChallengePeriodSet",
        "type": "event",
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "address", "name": "from", "type": "address"},
            {"indexed": True, "internalType": "address", "name": "fallbackDataProvider", "type": "address"},
        ],
        "name": "FallbackDataProviderSet",
        "type": "event",
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "address", "name": "from", "type": "address"},
            {"indexed": False, "internalType": "uint256", "name": "period", "type": "uint256"},
        ],
        "name": "FallbackSubmissionPeriodSet",
        "type": "event",
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "address", "name": "from", "type": "address"},
            {"indexed": False, "internalType": "uint256", "name": "pausedUntil", "type": "uint256"},
        ],
        "name": "PauseReturnCollateralSet",
        "type": "event",
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "address", "name": "from", "type": "address"},
            {"indexed": False, "internalType": "uint96", "name": "fee", "type": "uint96"},
        ],
        "name": "ProtocolFeeSet",
        "type": "event",
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "address", "name": "from", "type": "address"},
            {"indexed": False, "internalType": "uint256", "name": "period", "type": "uint256"},
        ],
        "name": "ReviewPeriodSet",
        "type": "event",
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "address", "name": "from", "type": "address"},
            {"indexed": False, "internalType": "uint96", "name": "fee", "type": "uint96"},
        ],
        "name": "SettlementFeeSet",
        "type": "event",
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "address", "name": "from", "type": "address"},
            {"indexed": False, "internalType": "uint256", "name": "period", "type": "uint256"},
        ],
        "name": "SubmissionPeriodSet",
        "type": "event",
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "address", "name": "from", "type": "address"},
            {"indexed": True, "internalType": "address", "name": "treasury", "type": "address"},
        ],
        "name": "TreasuryAddressSet",
        "type": "event",
    },
    {
        "inputs": [{"internalType": "uint256", "name": "_challengePeriod", "type": "uint256"}],
        "name": "setChallengePeriod",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [{"internalType": "address", "name": "_newFallbackDataProvider", "type": "address"}],
        "name": "setFallbackDataProvider",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [{"internalType": "uint256", "name": "_fallbackSubmissionPeriod", "type": "uint256"}],
        "name": "setFallbackSubmissionPeriod",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [{"internalType": "bool", "name": "_pause", "type": "bool"}],
        "name": "setPauseReturnCollateral",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [{"internalType": "uint96", "name": "_protocolFee", "type": "uint96"}],
        "name": "setProtocolFee",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [{"internalType": "uint256", "name": "_reviewPeriod", "type": "uint256"}],
        "name": "setReviewPeriod",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [{"internalType": "uint96", "name": "_settlementFee", "type": "uint96"}],
        "name": "setSettlementFee",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [{"internalType": "uint256", "name": "_submissionPeriod", "type": "uint256"}],
        "name": "setSubmissionPeriod",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [{"internalType": "address", "name": "_newTreasury", "type": "address"}],
        "name": "setTreasuryAddress",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "uint256", "name": "poolId", "type": "uint256"},
            {"indexed": True, "internalType": "address", "name": "from", "type": "address"},
            {"indexed": False, "internalType": "uint256", "name": "collateralAmount", "type": "uint256"},
        ],
        "name": "LiquidityAdded",
        "type": "event",
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "uint256", "name": "poolId", "type": "uint256"},
            {"indexed": True, "internalType": "address", "name": "from", "type": "address"},
            {"indexed": False, "internalType": "uint256", "name": "collateralAmount", "type": "uint256"},
        ],
        "name": "LiquidityRemoved",
        "type": "event",
    },
    {
        "inputs": [
            {"internalType": "uint256", "name": "_poolId", "type": "uint256"},
            {"internalType": "uint256", "name": "_collateralAmountIncr", "type": "uint256"},
        ],
        "name": "addLiquidity",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [
            {"internalType": "uint256", "name": "_poolId", "type": "uint256"},
            {"internalType": "uint256", "name": "_amount", "type": "uint256"},
        ],
        "name": "removeLiquidity",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "address", "name": "previousOwner", "type": "address"},
            {"indexed": True, "internalType": "address", "name": "newOwner", "type": "address"},
        ],
        "name": "OwnershipTransferred",
        "type": "event",
    },
    {
        "inputs": [],
        "name": "owner",
        "outputs": [{"internalType": "address", "name": "owner_", "type": "address"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [{"internalType": "address", "name": "_newOwner", "type": "address"}],
        "name": "transferOwnership",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "uint256", "name": "poolId", "type": "uint256"},
            {"indexed": True, "internalType": "address", "name": "from", "type": "address"},
            {"indexed": False, "internalType": "uint256", "name": "collateralAmount", "type": "uint256"},
        ],
        "name": "PoolIssued",
        "type": "event",
    },
    {
        "inputs": [
            {
                "components": [
                    {"internalType": "string", "name": "referenceAsset", "type": "string"},
                    {"internalType": "uint96", "name": "expiryTime", "type": "uint96"},
                    {"internalType": "uint256", "name": "floor", "type": "uint256"},
                    {"internalType": "uint256", "name": "inflection", "type": "uint256"},
                    {"internalType": "uint256", "name": "cap", "type": "uint256"},
                    {"internalType": "uint256", "name": "gradient", "type": "uint256"},
                    {"internalType": "uint256", "name": "collateralAmount", "type": "uint256"},
                    {"internalType": "address", "name": "collateralToken", "type": "address"},
                    {"internalType": "address", "name": "dataProvider", "type": "address"},
                    {"internalType": "uint256", "name": "capacity", "type": "uint256"},
                ],
                "internalType": "struct IPool.PoolParams",
                "name": "_poolParams",
                "type": "tuple",
            }
        ],
        "name": "createContingentPool",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "anonymous": False,
        "inputs": [
            {
                "indexed": True,
                "internalType": "enum LibDiamond.Status",
                "name": "statusFinalReferenceValue",
                "type": "uint8",
            },
            {"indexed": True, "internalType": "address", "name": "by", "type": "address"},
            {"indexed": True, "internalType": "uint256", "name": "poolId", "type": "uint256"},
            {"indexed": False, "internalType": "uint256", "name": "proposedFinalReferenceValue", "type": "uint256"},
        ],
        "name": "StatusChanged",
        "type": "event",
    },
    {
        "inputs": [
            {"internalType": "uint256", "name": "_poolId", "type": "uint256"},
            {"internalType": "uint256", "name": "_proposedFinalReferenceValue", "type": "uint256"},
        ],
        "name": "challengeFinalReferenceValue",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [
            {"internalType": "address", "name": "_positionToken", "type": "address"},
            {"internalType": "uint256", "name": "_amount", "type": "uint256"},
        ],
        "name": "redeemPositionToken",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [
            {"internalType": "bytes32", "name": "_poolId", "type": "bytes32"},
        ],
        "name": "setFinalReferenceValue",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "getMinPeriodUndisputed",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
]
