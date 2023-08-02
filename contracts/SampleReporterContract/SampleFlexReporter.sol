// SPDX-License-Identifier: MIT
pragma solidity ^0.8.15;

interface IFlex {
    function balanceOf(address account) external view returns (uint256);

    function allowance(
        address _user,
        address _spender
    ) external view returns (uint256);

    function approve(address _spender, uint256 _amount) external returns (bool);

    function transfer(
        address recipient,
        uint256 amount
    ) external returns (bool);

    function transferFrom(
        address sender,
        address recipient,
        uint256 amount
    ) external returns (bool);

    function depositStake(uint256 _amount) external;

    function requestStakingWithdraw(uint256 _amount) external;

    function getCurrentTip(bytes32 _queryId) external view returns (uint256);

    function submitValue(
        bytes32 _queryId,
        bytes calldata _value,
        uint256 _nonce,
        bytes memory _queryData
    ) external;

    function withdrawStake() external;

    function stakeAmount() external view returns (uint256);

    function getStakerInfo(
        address _staker
    )
        external
        view
        returns (
            uint256,
            uint256,
            uint256,
            uint256,
            uint256,
            uint256,
            uint256,
            uint256,
            uint256
        );

    function getNewValueCountbyQueryId(
        bytes32 _queryId
    ) external view returns (uint256);
}

contract SampleFlexReporter {
    IFlex public oracle;
    IFlex public autopay;
    IFlex public token;
    address public owner;
    uint256 public profitThreshold; //inTRB

    constructor(
        address _oracle,
        address _autopay,
        address _token,
        uint256 _profitThreshold
    ) {
        oracle = IFlex(_oracle);
        autopay = IFlex(_autopay);
        token = IFlex(_token);
        owner = msg.sender;
        profitThreshold = _profitThreshold;
    }

    modifier onlyOwner() {
        require(msg.sender == owner, "Only owner can call this function.");
        _;
    }

    function changeOwner(address _newOwner) external onlyOwner {
        owner = _newOwner;
    }

    function depositStake(uint256 _amount) external onlyOwner {
        oracle.depositStake(_amount);
    }

    function requestStakingWithdraw(uint256 _amount) external onlyOwner {
        oracle.requestStakingWithdraw(_amount);
    }

    function submitValue(
        bytes32 _queryId,
        bytes memory _value,
        uint256 _nonce,
        bytes memory _queryData
    ) external onlyOwner {
        uint256 _reward;
        _reward = autopay.getCurrentTip(_queryId);
        require(_reward > profitThreshold, "profit threshold not met");
        oracle.submitValue(_queryId, _value, _nonce, _queryData);
    }

    function submitValueBypass(
        bytes32 _queryId,
        bytes memory _value,
        uint256 _nonce,
        bytes memory _queryData
    ) external onlyOwner {
        oracle.submitValue(_queryId, _value, _nonce, _queryData);
    }

    function transfer(address _to, uint256 _amount) external onlyOwner {
        token.transfer(_to, _amount);
    }

    function balanceOf(address account) external view returns (uint256) {
        return token.balanceOf(address(this));
    }

    function allowance(
        address owner,
        address spender
    ) external view returns (uint256) {
        return token.allowance(address(this), address(oracle));
    }

    function approve(address spender, uint256 amount) external onlyOwner {
        token.approve(address(oracle), amount);
    }

    function withdrawStake() external onlyOwner {
        oracle.withdrawStake();
    }

    function getStakeAmount() external view returns (uint256) {
        return oracle.stakeAmount();
    }

    function getStakerInfo(
        address _stakerAddress
    )
        external
        view
        returns (
            uint256,
            uint256,
            uint256,
            uint256,
            uint256,
            uint256,
            uint256,
            uint256,
            uint256
        )
    {
        return oracle.getStakerInfo(address(this));
    }

    function getNewValueCountbyQueryId(
        bytes32 _queryId
    ) external view returns (uint256) {
        return oracle.getNewValueCountbyQueryId(_queryId);
    }

    receive() external payable {}
}
