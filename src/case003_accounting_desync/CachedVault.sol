// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import {FeeToken} from "./FeeToken.sol";

/// @title CachedVault
/// @notice Single-asset vault that tracks a cached `cachedTotal` of assets.
///         Ground-truth vulnerability: accounting desync. deposit() credits the
///         REQUESTED amount to the cache, not the amount actually received, so a
///         fee-on-transfer asset makes the cache overstate real holdings -- and
///         the final withdrawer cannot be paid. See bench/case003.json.
contract CachedVault {
    FeeToken public immutable token;
    uint256 public cachedTotal;
    mapping(address => uint256) public deposited;

    constructor(FeeToken _token) {
        token = _token;
    }

    /// @dev VULNERABLE: cachedTotal is incremented by `amt` (the requested amount)
    ///      rather than the real balance delta. With a fee-on-transfer token the
    ///      vault receives less than `amt`, so cachedTotal drifts above the true
    ///      balance and the conservation invariant (cachedTotal == balance) breaks.
    function deposit(uint256 amt) external {
        token.transferFrom(msg.sender, address(this), amt);
        cachedTotal += amt;
        deposited[msg.sender] += amt;
    }

    function withdraw() external {
        uint256 amt = deposited[msg.sender];
        deposited[msg.sender] = 0;
        cachedTotal -= amt;
        token.transfer(msg.sender, amt);
    }
}
