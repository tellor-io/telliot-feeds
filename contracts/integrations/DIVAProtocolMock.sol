// SPDX-License-Identifier: MIT
pragma solidity ^0.8.10;

contract DIVAProtocolMock {
    mapping(bytes32 => Pool) private pools;

    enum Status {
        Open,
        Submitted,
        Challenged,
        Confirmed
    }

    struct Pool {
        uint256 floor;
        uint256 inflection;
        uint256 cap;
        uint256 gradient;
        uint256 collateralBalance;
        uint256 finalReferenceValue;
        uint256 capacity;
        uint256 statusTimestamp;
        address shortToken;
        uint256 payoutShort;
        address longToken;
        uint256 payoutLong;
        address collateralToken;
        uint256 expiryTime;
        address dataProvider;
        uint256 protocolFee;
        uint256 settlementFee;
        Status statusFinalReferenceValue;
        string referenceAsset;
    }

    // Add some fake pools
    constructor() {
        Pool memory fakePool;

        fakePool.referenceAsset = "ETH/USD";
        fakePool.expiryTime = 1657349074;
        fakePool.floor = 2000000000000000000000;
        fakePool.inflection = 2000000000000000000000;
        fakePool.cap = 4500000000000000000000;
        fakePool.collateralToken = 0x867e53feDe91d27101E062BF7002143EbaEA3e30;
        fakePool.collateralBalance = 214199598796389167516;
        fakePool.shortToken = 0x91E75Aebda86a6B02d5510438f2981AC4Af1A44d;
        fakePool.longToken = 0x945b1fA4DB6Fb1f8d3C7501968F6549C8c147D4e;
        fakePool.finalReferenceValue = 0;
        fakePool.statusFinalReferenceValue = Status.Open;
        fakePool.statusTimestamp = 1647349398;
        fakePool.dataProvider = 0xED6D661645a11C45F4B82274db677867a7D32675;
        fakePool.settlementFee = 500000000000000;
        fakePool.capacity = 0;

        bytes32 _poolId = 0x0ccf69d6832bcb70d201cd5d4014799d4e5b9944d7644522bfabecfe147ec2a0;
        pools[_poolId] = fakePool;


    }

    function addPool(bytes32 _poolId, Pool calldata _poolParams
        ) public returns (Pool memory) {
        pools[_poolId] = _poolParams;
        return pools[_poolId];
    }

    /*
     * @notice Returns the pool parameters for a given pool Id
     * @param _poolId Id of the pool
     * @return Pool struct
     */
    function getPoolParameters(bytes32 _poolId)
        external
        view
        returns (Pool memory)
    {
        return pools[_poolId];
    }

    function changePoolExpiry(bytes32 _poolId, uint256 _expiryTime) public {
        pools[_poolId].expiryTime = _expiryTime;
    }
}
