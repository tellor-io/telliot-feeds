// SPDX-License-Identifier: MIT
pragma solidity ^0.8.10;

contract DIVAProtocolMock {
    // Settlement status
    mapping(address => mapping(address => uint256)) public feeClaims; // mapping token address to claimant address to amount
    mapping(uint256 => Pool) private pools;

    enum Status {
        Open,
        Submitted,
        Challenged,
        Confirmed
    }

    struct Pool {
        string referenceAsset; // Reference asset string (e.g., "BTC/USD", "ETH Gas Price (Wei)", "TVL Locked in DeFi", etc.)
        uint256 expiryTime; // Expiration time of the pool and as of time of final value expressed as a unix timestamp in seconds
        uint256 floor; // Reference asset value at or below which all collateral will end up in the short pool
        uint256 inflection; // Threshold for rebalancing between the long and the short side of the pool
        uint256 cap; // Reference asset value at or above which all collateral will end up in the long pool
        uint256 supplyInitial; // Initial short and long token supply
        address collateralToken; // Address of ERC20 collateral token
        uint256 collateralBalanceShortInitial; // Collateral balance of short side at pool creation
        uint256 collateralBalanceLongInitial; // Collateral balance of long side at pool creation
        uint256 collateralBalance; // Current total pool collateral balance
        address shortToken; // Short position token address
        address longToken; // Long position token address
        uint256 finalReferenceValue; // Reference asset value at the time of expiration
        Status statusFinalReferenceValue; // Status of final reference price (0 = Open, 1 = Submitted, 2 = Challenged, 3 = Confirmed)
        uint256 redemptionAmountLongToken; // Payout amount per long position token
        uint256 redemptionAmountShortToken; // Payout amount per short position token
        uint256 statusTimestamp; // Timestamp of status change
        address dataProvider; // Address of data provider
        uint256 redemptionFee; // Redemption fee prevailing at the time of pool creation
        uint256 settlementFee; // Settlement fee prevailing at the time of pool creation
        uint256 capacity; // Maximum collateral that the pool can accept; 0 for unlimited
    }

    // Add some fake pools
    constructor() {
        Pool memory fakePool;

        fakePool.referenceAsset = "ETH/USD";
        fakePool.expiryTime = 1657349074;
        fakePool.floor = 2000000000000000000000;
        fakePool.inflection = 2000000000000000000000;
        fakePool.cap = 4500000000000000000000;
        fakePool.supplyInitial = 100000000000000000000;
        fakePool.collateralToken = 0x867e53feDe91d27101E062BF7002143EbaEA3e30;
        fakePool.collateralBalanceShortInitial = 50000000000000000000;
        fakePool.collateralBalanceLongInitial = 50000000000000000000;
        fakePool.collateralBalance = 214199598796389167516;
        fakePool.shortToken = 0x91E75Aebda86a6B02d5510438f2981AC4Af1A44d;
        fakePool.longToken = 0x945b1fA4DB6Fb1f8d3C7501968F6549C8c147D4e;
        fakePool.finalReferenceValue = 0;
        fakePool.statusFinalReferenceValue = Status.Open;
        fakePool.redemptionAmountLongToken = 0;
        fakePool.redemptionAmountShortToken = 0;
        fakePool.statusTimestamp = 1647349398;
        fakePool.dataProvider = 0xED6D661645a11C45F4B82274db677867a7D32675;
        fakePool.redemptionFee = 2500000000000000;
        fakePool.settlementFee = 500000000000000;
        fakePool.capacity = 0;

        pools[3] = fakePool;

        Pool memory fakePool2;

        fakePool2.referenceAsset = "BTC/USD";
        fakePool2.expiryTime = 1654700353;
        fakePool2.floor = 2000000000000000000000;
        fakePool2.inflection = 2000000000000000000000;
        fakePool2.cap = 4500000000000000000000;
        fakePool2.supplyInitial = 100000000000000000000;
        fakePool2.collateralToken = 0xc778417E063141139Fce010982780140Aa0cD5Ab;
        fakePool2.collateralBalanceShortInitial = 50000000000000000000;
        fakePool2.collateralBalanceLongInitial = 50000000000000000000;
        fakePool2.collateralBalance = 214199598796389167516;
        fakePool2.shortToken = 0x91E75Aebda86a6B02d5510438f2981AC4Af1A44d;
        fakePool2.longToken = 0x945b1fA4DB6Fb1f8d3C7501968F6549C8c147D4e;
        fakePool2.finalReferenceValue = 0;
        fakePool2.statusFinalReferenceValue = Status.Open;
        fakePool2.redemptionAmountLongToken = 0;
        fakePool2.redemptionAmountShortToken = 0;
        fakePool2.statusTimestamp = 1647349398;
        fakePool2.dataProvider = 0xED6D661645a11C45F4B82274db677867a7D32675;
        fakePool2.redemptionFee = 2500000000000000;
        fakePool2.settlementFee = 500000000000000;
        fakePool2.capacity = 0;

        pools[10] = fakePool2;
    }

    /**
     * @notice Returns the pool parameters for a given pool Id
     * @param _poolId Id of the pool
     * @return Pool struct
     */
    function getPoolParameters(uint256 _poolId)
        external
        view
        returns (Pool memory)
    {
        Pool storage _pool = pools[_poolId];
        return _pool;
    }

    function changePoolExpiry(uint256 _poolId, uint256 _timestamp)
        external
        returns (uint256)
    {
        pools[_poolId].expiryTime = _timestamp;
        return pools[_poolId].expiryTime;
    }
}
