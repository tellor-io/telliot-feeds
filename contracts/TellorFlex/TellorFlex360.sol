// SPDX-License-Identifier: MIT
pragma solidity 0.8.3;

import "../../interfaces/IERC20.sol";

/**
 @author Tellor Inc.
 @title TellorFlex
 @dev This is a streamlined Tellor oracle system which handles staking, reporting,
 * slashing, and user data getters in one contract. This contract is controlled
 * by a single address known as 'governance', which could be an externally owned
 * account or a contract, allowing for a flexible, modular design.
*/
contract TellorFlex360 {
    // Storage
    IERC20 public token; // token used for staking and rewards
    address public governance; // address with ability to remove values and slash reporters
    address public owner; // contract deployer, can call init function once
    uint256 public accumulatedRewardPerShare; // accumulated staking reward per staked token
    uint256 public reportingLock; // base amount of time before a reporter is able to submit a value again
    uint256 public rewardRate; // total staking rewards released per second
    uint256 public stakeAmount; // minimum amount required to be a staker
    uint256 public stakeAmountDollarTarget; // amount of US dollars required to be a staker
    uint256 public stakingRewardsBalance; // total amount of staking rewards
    bytes32 public stakingTokenPriceQueryId; // staking token SpotPrice queryId, used for updating stakeAmount
    uint256 public timeBasedReward = 5e17; // amount of TB rewards released per 5 minutes
    uint256 public timeOfLastAllocation; // time of last update to accumulatedRewardPerShare
    uint256 public timeOfLastNewValue = block.timestamp; // time of the last new submitted value, originally set to the block timestamp
    uint256 public totalRewardDebt; // staking reward debt, used to calculate real staking rewards balance
    uint256 public totalStakeAmount; // total amount of tokens locked in contract (via stake)
    uint256 public totalStakers; // total number of stakers with at least stakeAmount staked, not exact

    mapping(bytes32 => Report) private reports; // mapping of query IDs to a report
    mapping(address => StakeInfo) private stakerDetails; // mapping from a persons address to their staking info

    // Structs
    struct Report {
        uint256[] timestamps; // array of all newValueTimestamps reported
        mapping(uint256 => uint256) timestampIndex; // mapping of timestamps to respective indices
        mapping(uint256 => uint256) timestampToBlockNum; // mapping of timestamp to block number
        mapping(uint256 => bytes) valueByTimestamp; // mapping of timestamps to values
        mapping(uint256 => address) reporterByTimestamp; // mapping of timestamps to reporters
        mapping(uint256 => bool) isDisputed;
    }

    struct StakeInfo {
        uint256 startDate; // stake or withdrawal request start date
        uint256 stakedBalance; // staked token balance
        uint256 lockedBalance; // amount locked for withdrawal
        uint256 rewardDebt; // used for staking reward calculation
        uint256 reporterLastTimestamp; // timestamp of reporter's last reported value
        uint256 reportsSubmitted; // total number of reports submitted by reporter
        uint256 startVoteCount; // total number of governance votes when stake deposited
        uint256 startVoteTally; // staker vote tally when stake deposited
        bool staked; // used to keep track of total stakers
        mapping(bytes32 => uint256) reportsSubmittedByQueryId; // mapping of queryId to number of reports submitted by reporter
    }

    // Functions
    /**
     * @dev Initializes system parameters
     * @param _token address of token used for staking and rewards
     * @param _reportingLock base amount of time (seconds) before reporter is able to report again
     * @param _stakeAmountDollarTarget fixed USD amount that stakeAmount targets on updateStakeAmount
     * @param _stakingTokenPrice current price of staking token in USD (18 decimals)
     * @param _stakingTokenPriceQueryId queryId where staking token price is reported
     */
    constructor(
        address _token,
        uint256 _reportingLock,
        uint256 _stakeAmountDollarTarget,
        uint256 _stakingTokenPrice,
        bytes32 _stakingTokenPriceQueryId
    ) {
        require(_token != address(0), "must set token address");
        require(_stakingTokenPrice > 0, "must set staking token price");
        require(_reportingLock > 0, "must set reporting lock");
        require(_stakingTokenPriceQueryId != bytes32(0), "must set staking token price queryId");
        token = IERC20(_token);
        owner = msg.sender;
        reportingLock = _reportingLock;
        stakeAmountDollarTarget = _stakeAmountDollarTarget;
        stakeAmount = (_stakeAmountDollarTarget * 1e18) / _stakingTokenPrice;
        stakingTokenPriceQueryId = _stakingTokenPriceQueryId;
    }

    /**
     * @dev Allows the owner to initialize the governance (flex addy needed for governance deployment)
     * @param _governanceAddress address of governance contract (github.com/tellor-io/governance)
     */
    function init(address _governanceAddress) external {
        // require(msg.sender == owner, "only owner can set governance address");
        require(governance == address(0), "governance address already set");
        require(
            _governanceAddress != address(0),
            "governance address can't be zero address"
        );
        governance = _governanceAddress;
    }

    /**
     * @dev Allows a reporter to submit stake
     * @param _amount amount of tokens to stake
     */
    function depositStake(uint256 _amount) external {
        require(governance != address(0), "governance address not set");
        StakeInfo storage _staker = stakerDetails[msg.sender];
        uint256 _stakedBalance = _staker.stakedBalance;
        uint256 _lockedBalance = _staker.lockedBalance;
        if (_lockedBalance > 0) {
            if (_lockedBalance >= _amount) {
                // if staker's locked balance covers full _amount, use that
                _staker.lockedBalance -= _amount;
            } else {
                // otherwise, stake the whole locked balance and transfer the
                // remaining amount from the staker's address
                require(
                    token.transferFrom(
                        msg.sender,
                        address(this),
                        _amount - _lockedBalance
                    )
                );
                _staker.lockedBalance = 0;
            }
            require(token.transferFrom(msg.sender, address(this), _amount));
        }
        _updateStakeAndPayRewards(msg.sender, _stakedBalance + _amount);
        _staker.startDate = block.timestamp; // This resets the staker start date to now
    }

    /**
     * @dev Allows a reporter to submit a value to the oracle
     * @param _queryId is ID of the specific data feed. Equals keccak256(_queryData) for non-legacy IDs
     * @param _value is the value the user submits to the oracle
     * @param _nonce is the current value count for the query id
     * @param _queryData is the data used to fulfill the data query
     */
    function submitValue(
        bytes32 _queryId,
        bytes calldata _value,
        uint256 _nonce,
        bytes calldata _queryData
    ) external {
        require(keccak256(_value) != keccak256(""), "value must be submitted");
        Report storage _report = reports[_queryId];
        require(
            _nonce == _report.timestamps.length || _nonce == 0,
            "nonce must match timestamp index"
        );
        StakeInfo storage _staker = stakerDetails[msg.sender];
        require(
            _staker.stakedBalance >= stakeAmount,
            "balance must be greater than stake amount"
        );
        // Require reporter to abide by given reporting lock
        require(
            (block.timestamp - _staker.reporterLastTimestamp) * 1000 >
                (reportingLock * 1000) / (_staker.stakedBalance / stakeAmount),
            "still in reporter time lock, please wait!"
        );
        require(
            _queryId == keccak256(_queryData) || uint256(_queryId) <= 100,
            "query id must be hash of query data"
        );
        _staker.reporterLastTimestamp = block.timestamp;
        // Checks for no double reporting of timestamps
        require(
            _report.reporterByTimestamp[block.timestamp] == address(0),
            "timestamp already reported for"
        );
        // Update number of timestamps, value for given timestamp, and reporter for timestamp
        _report.timestampIndex[block.timestamp] = _report.timestamps.length;
        _report.timestamps.push(block.timestamp);
        _report.timestampToBlockNum[block.timestamp] = block.number;
        _report.valueByTimestamp[block.timestamp] = _value;
        _report.reporterByTimestamp[block.timestamp] = msg.sender;
        // Disperse Time Based Reward
        uint256 _reward = ((block.timestamp - timeOfLastNewValue) * timeBasedReward) / 300; //.5 TRB per 5 minutes
        timeOfLastNewValue = block.timestamp;
        _staker.reportsSubmitted++;
        _staker.reportsSubmittedByQueryId[_queryId]++;
    }

    /**
     * @dev Updates the stake amount after retrieving the latest
     * 12+-hour-old staking token price from the oracle
     */
    function updateStakeAmount(uint256 _amount) external{
            stakeAmount = _amount;
        }
    // *****************************************************************************
    // *                                                                           *
    // *                               Getters                                     *
    // *                                                                           *
    // *****************************************************************************

    /**
     * @dev Retrieves the latest value for the queryId before the specified timestamp
     * @param _queryId is the queryId to look up the value for
     * @param _timestamp before which to search for latest value
     * @return _ifRetrieve bool true if able to retrieve a non-zero value
     * @return _value the value retrieved
     * @return _timestampRetrieved the value's timestamp
     */
    function getDataBefore(bytes32 _queryId, uint256 _timestamp)
        public
        view
        returns (
            bool _ifRetrieve,
            bytes memory _value,
            uint256 _timestampRetrieved
        )
    {
        (bool _found, uint256 _index) = getIndexForDataBefore(
            _queryId,
            _timestamp
        );
        if (!_found) return (false, bytes(""), 0);
        _timestampRetrieved = getTimestampbyQueryIdandIndex(_queryId, _index);
        _value = retrieveData(_queryId, _timestampRetrieved);
        return (true, _value, _timestampRetrieved);
    }

    /**
     * @dev Counts the number of values that have been submitted for the request.
     * @param _queryId the id to look up
     * @return uint256 count of the number of values received for the id
     */
    function getNewValueCountbyQueryId(bytes32 _queryId)
        public
        view
        returns (uint256)
    {
        return reports[_queryId].timestamps.length;
    }

    /**
     * @dev Returns the real staking rewards balance after accounting for unclaimed rewards
     * @return uint256 real staking rewards balance
     */
    function getRealStakingRewardsBalance() external view returns (uint256) {
        uint256 _pendingRewards = (_getUpdatedAccumulatedRewardPerShare() *
            totalStakeAmount) /
            1e18 -
            totalRewardDebt;
        return (stakingRewardsBalance - _pendingRewards);
    }

    /**
     * @dev Returns reporter address and whether a value was removed for a given queryId and timestamp
     * @param _queryId the id to look up
     * @param _timestamp is the timestamp of the value to look up
     * @return address reporter who submitted the value
     * @return bool true if the value was removed
     */
    function getReportDetails(bytes32 _queryId, uint256 _timestamp)
        external
        view
        returns (address, bool)
    {
        return (reports[_queryId].reporterByTimestamp[_timestamp], reports[_queryId].isDisputed[_timestamp]);
    }

    /**
     * @dev Returns the address of the reporter who submitted a value for a data ID at a specific time
     * @param _queryId is ID of the specific data feed
     * @param _timestamp is the timestamp to find a corresponding reporter for
     * @return address of the reporter who reported the value for the data ID at the given timestamp
     */
    function getReporterByTimestamp(bytes32 _queryId, uint256 _timestamp)
        external
        view
        returns (address)
    {
        return reports[_queryId].reporterByTimestamp[_timestamp];
    }

    /**
     * @dev Returns the timestamp of the reporter's last submission
     * @param _reporter is address of the reporter
     * @return uint256 timestamp of the reporter's last submission
     */
    function getReporterLastTimestamp(address _reporter)
        external
        view
        returns (uint256)
    {
        return stakerDetails[_reporter].reporterLastTimestamp;
    }

    /**
     * @dev Returns the reporting lock time, the amount of time a reporter must wait to submit again
     * @return uint256 reporting lock time
     */
    function getReportingLock() external view returns (uint256) {
        return reportingLock;
    }

    /**
     * @dev Returns the number of values submitted by a specific reporter address
     * @param _reporter is the address of a reporter
     * @return uint256 the number of values submitted by the given reporter
     */
    function getReportsSubmittedByAddress(address _reporter)
        external
        view
        returns (uint256)
    {
        return stakerDetails[_reporter].reportsSubmitted;
    }

    /**
     * @dev Returns the number of values submitted to a specific queryId by a specific reporter address
     * @param _reporter is the address of a reporter
     * @param _queryId is the ID of the specific data feed
     * @return uint256 the number of values submitted by the given reporter to the given queryId
     */
    function getReportsSubmittedByAddressAndQueryId(
        address _reporter,
        bytes32 _queryId
    ) external view returns (uint256) {
        return stakerDetails[_reporter].reportsSubmittedByQueryId[_queryId];
    }

    /**
     * @dev Returns amount required to report oracle values
     * @return uint256 stake amount
     */
    function getStakeAmount() external view returns (uint256) {
        return stakeAmount;
    }

    /**
     * @dev Returns all information about a staker
     * @param _stakerAddress address of staker inquiring about
     * @return uint startDate of staking
     * @return uint current amount staked
     * @return uint current amount locked for withdrawal
     * @return uint reward debt used to calculate staking rewards
     * @return uint reporter's last reported timestamp
     * @return uint total number of reports submitted by reporter
     * @return uint governance vote count when first staked
     * @return uint number of votes cast by staker when first staked
     * @return bool whether staker is counted in totalStakers
     */
    function getStakerInfo(address _stakerAddress)
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
            bool
        )
    {
        StakeInfo storage _staker = stakerDetails[_stakerAddress];
        return (
            _staker.startDate,
            _staker.stakedBalance,
            _staker.lockedBalance,
            _staker.rewardDebt,
            _staker.reporterLastTimestamp,
            _staker.reportsSubmitted,
            _staker.startVoteCount,
            _staker.startVoteTally,
            _staker.staked
        );
    }

    /**
     * @dev Returns the timestamp for the last value of any ID from the oracle
     * @return uint256 timestamp of the last oracle value
     */
    function getTimeOfLastNewValue() external view returns (uint256) {
        return timeOfLastNewValue;
    }

    /**
     * @dev Gets the timestamp for the value based on their index
     * @param _queryId is the id to look up
     * @param _index is the value index to look up
     * @return uint256 timestamp
     */
    function getTimestampbyQueryIdandIndex(bytes32 _queryId, uint256 _index)
        public
        view
        returns (uint256)
    {
        return reports[_queryId].timestamps[_index];
    }

    /**
     * @dev Retrieves latest array index of data before the specified timestamp for the queryId
     * @param _queryId is the queryId to look up the index for
     * @param _timestamp is the timestamp before which to search for the latest index
     * @return _found whether the index was found
     * @return _index the latest index found before the specified timestamp
     */
    // slither-disable-next-line calls-loop
    function getIndexForDataBefore(bytes32 _queryId, uint256 _timestamp)
        public
        view
        returns (bool _found, uint256 _index)
    {
        uint256 _count = getNewValueCountbyQueryId(_queryId);
        if (_count > 0) {
            uint256 _middle;
            uint256 _start = 0;
            uint256 _end = _count - 1;
            uint256 _time;
            //Checking Boundaries to short-circuit the algorithm
            _time = getTimestampbyQueryIdandIndex(_queryId, _start);
            if (_time >= _timestamp) return (false, 0);
            _time = getTimestampbyQueryIdandIndex(_queryId, _end);
            if (_time < _timestamp) {
                while(isInDispute(_queryId, _time) && _end > 0) {
                    _end--;
                    _time = getTimestampbyQueryIdandIndex(_queryId, _end);
                }
                if(_end == 0 && isInDispute(_queryId, _time)) {
                    return (false, 0);
                }
                return (true, _end);
            }
            //Since the value is within our boundaries, do a binary search
            while (true) {
                _middle = (_end - _start) / 2 + 1 + _start;
                _time = getTimestampbyQueryIdandIndex(_queryId, _middle);
                if (_time < _timestamp) {
                    //get immediate next value
                    uint256 _nextTime = getTimestampbyQueryIdandIndex(
                        _queryId,
                        _middle + 1
                    );
                    if (_nextTime >= _timestamp) {
                        if(!isInDispute(_queryId, _time)) {
                            // _time is correct
                            return (true, _middle);
                        } else {
                            // iterate backwards until we find a non-disputed value
                            while(isInDispute(_queryId, _time) && _middle > 0) {
                                _middle--;
                                _time = getTimestampbyQueryIdandIndex(_queryId, _middle);
                            }
                            if(_middle == 0 && isInDispute(_queryId, _time)) {
                                return (false, 0);
                            }
                            // _time is correct
                            return (true, _middle);
                        }
                    } else {
                        //look from middle + 1(next value) to end
                        _start = _middle + 1;
                    }
                } else {
                    uint256 _prevTime = getTimestampbyQueryIdandIndex(
                        _queryId,
                        _middle - 1
                    );
                    if (_prevTime < _timestamp) {
                        if(!isInDispute(_queryId, _prevTime)) {
                            // _prevTime is correct
                            return (true, _middle - 1);
                        } else {
                            // iterate backwards until we find a non-disputed value
                            _middle--;
                            while(isInDispute(_queryId, _prevTime) && _middle > 0) {
                                _middle--;
                                _prevTime = getTimestampbyQueryIdandIndex(
                                    _queryId,
                                    _middle
                                );
                            }
                            if(_middle == 0 && isInDispute(_queryId, _prevTime)) {
                                return (false, 0);
                            }
                            // _prevtime is correct
                            return (true, _middle);
                        }
                    } else {
                        //look from start to middle -1(prev value)
                        _end = _middle - 1;
                    }
                }
            }
        }
        return (false, 0);
    }

    /**
     * @dev Returns total balance of time based rewards in contract
     * @return uint256 amount of trb
     */
    function getTotalTimeBasedRewardsBalance() external view returns (uint256) {
        return token.balanceOf(address(this)) - (totalStakeAmount + stakingRewardsBalance);
    }

    /**
     * @dev Returns whether a given value is disputed
     * @param _queryId unique ID of the data feed
     * @param _timestamp timestamp of the value
     * @return bool whether the value is disputed
     */
    function isInDispute(bytes32 _queryId, uint256 _timestamp)
        public
        view
        returns (bool)
    {
        return reports[_queryId].isDisputed[_timestamp];
    }

    /**
     * @dev Retrieve value from oracle based on timestamp
     * @param _queryId being requested
     * @param _timestamp to retrieve data/value from
     * @return bytes value for timestamp submitted
     */
    function retrieveData(bytes32 _queryId, uint256 _timestamp)
        public
        view
        returns (bytes memory)
    {
        return reports[_queryId].valueByTimestamp[_timestamp];
    }

    // *****************************************************************************
    // *                                                                           *
    // *                          Internal functions                               *
    // *                                                                           *
    // *****************************************************************************

    /**
     * @dev Updates accumulated staking rewards per staked token
     */
    function _updateRewards() internal {
        if (timeOfLastAllocation == block.timestamp) {
            return;
        }
        if (totalStakeAmount == 0 || rewardRate == 0) {
            timeOfLastAllocation = block.timestamp;
            return;
        }
        // calculate accumulated reward per token staked
        uint256 _newAccumulatedRewardPerShare = accumulatedRewardPerShare +
            ((block.timestamp - timeOfLastAllocation) * rewardRate * 1e18) /
            totalStakeAmount;
        // calculate accumulated reward with _newAccumulatedRewardPerShare
        uint256 _accumulatedReward = (_newAccumulatedRewardPerShare *
            totalStakeAmount) /
            1e18 -
            totalRewardDebt;
        if (_accumulatedReward >= stakingRewardsBalance) {
            // if staking rewards run out, calculate remaining reward per staked
            // token and set rewardRate to 0
            uint256 _newPendingRewards = stakingRewardsBalance -
                ((accumulatedRewardPerShare * totalStakeAmount) /
                    1e18 -
                    totalRewardDebt);
            accumulatedRewardPerShare +=
                (_newPendingRewards * 1e18) /
                totalStakeAmount;
            rewardRate = 0;
        } else {
            accumulatedRewardPerShare = _newAccumulatedRewardPerShare;
        }
        timeOfLastAllocation = block.timestamp;
    }

    /**
     * @dev Called whenever a user's stake amount changes. First updates staking rewards,
     * transfers pending rewards to user's address, and finally updates user's stake amount
     * and other relevant variables.
     * @param _stakerAddress address of user whose stake is being updated
     * @param _newStakedBalance new staked balance of user
     */
    function _updateStakeAndPayRewards(
        address _stakerAddress,
        uint256 _newStakedBalance
    ) internal {
        _updateRewards();
        StakeInfo storage _staker = stakerDetails[_stakerAddress];
        if (_staker.stakedBalance > 0) {
            // if address already has a staked balance, calculate and transfer pending rewards
            uint256 _pendingReward = (_staker.stakedBalance *
                accumulatedRewardPerShare) /
                1e18 -
                _staker.rewardDebt;
            stakingRewardsBalance -= _pendingReward;
            require(token.transfer(msg.sender, _pendingReward));
            totalRewardDebt -= _staker.rewardDebt;
            totalStakeAmount -= _staker.stakedBalance;
        }
        _staker.stakedBalance = _newStakedBalance;
        // Update total stakers
        if (_staker.stakedBalance >= stakeAmount) {
            if (_staker.staked == false) {
                totalStakers++;
            }
            _staker.staked = true;
        } else {
            if (_staker.staked == true && totalStakers > 0) {
                totalStakers--;
            }
            _staker.staked = false;
        }
        // tracks rewards accumulated before stake amount updated
        _staker.rewardDebt =
            (_staker.stakedBalance * accumulatedRewardPerShare) /
            1e18;
        totalRewardDebt += _staker.rewardDebt;
        totalStakeAmount += _staker.stakedBalance;
    }

    /**
     * @dev Internal function retrieves updated accumulatedRewardPerShare
     * @return uint256 up-to-date accumulated reward per share
     */
    function _getUpdatedAccumulatedRewardPerShare()
        internal
        view
        returns (uint256)
    {
        if (totalStakeAmount == 0) {
            return accumulatedRewardPerShare;
        }
        uint256 _newAccumulatedRewardPerShare = accumulatedRewardPerShare +
            ((block.timestamp - timeOfLastAllocation) * rewardRate * 1e18) /
            totalStakeAmount;
        uint256 _accumulatedReward = (_newAccumulatedRewardPerShare *
            totalStakeAmount) /
            1e18 -
            totalRewardDebt;
        if (_accumulatedReward >= stakingRewardsBalance) {
            uint256 _newPendingRewards = stakingRewardsBalance -
                ((accumulatedRewardPerShare * totalStakeAmount) /
                    1e18 -
                    totalRewardDebt);
            _newAccumulatedRewardPerShare =
                accumulatedRewardPerShare +
                (_newPendingRewards * 1e18) /
                totalStakeAmount;
        }
        return _newAccumulatedRewardPerShare;
    }
}
