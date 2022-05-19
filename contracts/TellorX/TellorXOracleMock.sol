// SPDX-Licence-Identifier: MIT
pragma solidity ^0.8.10;

contract TellorXOracleMock {
    function getReportTimestampByIndex(bytes32 _queryId, uint256 _index)
        public
        pure
        returns (uint256)
    {
        return 1234;
    }

    function getReportingLock() public pure returns (uint256) {
        return 12;
    }

    function getTimeBasedReward() public pure returns (uint256) {
        return 1e18;
    }

    function getCurrentReward(bytes32 _queryId)
        public
        pure
        returns (uint256[2] memory)
    {
        return [uint256(1e18), uint256(2e18)];
    }

    function getTimestampCountById(bytes32 _queryId)
        public
        pure
        returns (uint256)
    {
        return 30;
    }

    function getTimeOfLastNewValue() public pure returns (uint256) {
        return 123456789;
    }

    function getTipsById(bytes32 _queryId) public pure returns (uint256) {
        return 3e18;
    }

    function getReporterLastTimestamp(address _reporter)
        external
        view
        returns (uint256)
    {
        return 123456789;
    }

    function submitValue(
        bytes32 _queryId,
        bytes calldata _value,
        uint256 _nonce,
        bytes memory _queryData
    ) external {
    }
}
