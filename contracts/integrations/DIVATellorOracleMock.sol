// SPDX-License-Identifier: MIT
pragma solidity ^0.8.10;

import "../../interfaces/ITellor.sol";
import "./interfaces/IDIVADiamond.sol";

contract DIVATellorOracleMock {
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

    uint256 public minPeriodUndisputed;
    uint256 public currentChainId;
    ITellor public tellorOracle;
    IDIVADiamond public divaDiamond;
    bool public setFinalReferenceValueCalled = false;

    constructor(
        uint256 _minPeriodUndisputed,
        address _tellorOracle
    ) {
        minPeriodUndisputed = _minPeriodUndisputed;
        tellorOracle = ITellor(_tellorOracle);
    }

    function getMinPeriodUndisputed() public view returns (uint256) {
        return minPeriodUndisputed;
    }

    function updateMinPeriodUndisputed(uint256 _minPeriodUndisputed) external returns (uint256) {
        minPeriodUndisputed = _minPeriodUndisputed;
        return minPeriodUndisputed;
    }

    function updateCurrentChainId(uint256 _currentChainId) external returns (uint256) {
        currentChainId = _currentChainId;
        return currentChainId;
    }

    function setFinalReferenceValue(bytes32 _poolId, address _divaDiamond) public {
        // bytes32 queryId = keccak256(abi.encode(_poolId, _divaDiamond, currentChainId)); // goerli chain id is 5
        // uint256 reportTime = tellorOracle.getTimestampbyQueryIdandIndex(queryId, 0); // get timestamp of first value
        // uint256 poolExpiry = divaDiamond.getPoolParameters(_poolId).expiryTime;
        // require(reportTime > poolExpiry, "Report time must be after pool expiry time");
        // require(block.timestamp > reportTime + minPeriodUndisputed, "minPeriodUndisputed has not elapsed since report time");
        // address reporter = tellorOracle.getReporterByTimestamp(queryId, reportTime);
        // require(reporter == msg.sender, "Only the reporter can set the final reference value");
        // uint256 status = uint256(divaDiamond.updatePoolStatus(_poolId, 1)); // 1 = Submitted
        // return status;
        // setFinalReferenceValueCalled = true;
    }

    function checkPoolSettled() public view returns (bool) {
        return setFinalReferenceValueCalled;
    }
}
