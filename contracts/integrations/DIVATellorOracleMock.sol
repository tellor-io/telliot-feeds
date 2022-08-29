// SPDX-License-Identifier: MIT
pragma solidity ^0.8.10;

contract DIVATellorOracleMock {
    uint256 public minPeriodUndisputed;

    constructor(
        uint256 _minPeriodUndisputed
    ) {
        minPeriodUndisputed = _minPeriodUndisputed;
    }

    function getMinPeriodUndisputed() public view returns (uint256) {
        return minPeriodUndisputed;
    }

    function updateMinPeriodUndisputed(uint256 _minPeriodUndisputed) external returns (uint256) {
        minPeriodUndisputed = _minPeriodUndisputed;
        return minPeriodUndisputed;
    }
}
