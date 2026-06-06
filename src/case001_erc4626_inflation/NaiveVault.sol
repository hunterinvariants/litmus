// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import {MockERC20} from "../common/MockERC20.sol";

/// @title NaiveVault
/// @notice Minimal ERC4626-style vault WITHOUT virtual-shares / dead-shares
///         protection. Ground-truth vulnerability: first-depositor share
///         inflation (rounding / precision). See bench/case001.json.
contract NaiveVault {
    MockERC20 public immutable asset;
    uint256 public totalShares;
    mapping(address => uint256) public shares;

    constructor(MockERC20 _asset) {
        asset = _asset;
    }

    function totalAssets() public view returns (uint256) {
        return asset.balanceOf(address(this));
    }

    /// @dev VULNERABLE: shares are minted pro-rata against the LIVE totalAssets()
    ///      with no virtual offset. The first depositor mints 1 share, donates
    ///      assets directly to the vault to inflate the share price, and a later
    ///      depositor's shares round down to zero — handing their assets over.
    function deposit(uint256 assets) external returns (uint256 minted) {
        uint256 supply = totalShares;
        if (supply == 0) {
            minted = assets;
        } else {
            minted = (assets * supply) / totalAssets();
        }
        asset.transferFrom(msg.sender, address(this), assets);
        totalShares += minted;
        shares[msg.sender] += minted;
    }

    function redeem(uint256 shareAmount) external returns (uint256 assets) {
        assets = (shareAmount * totalAssets()) / totalShares;
        shares[msg.sender] -= shareAmount;
        totalShares -= shareAmount;
        asset.transfer(msg.sender, assets);
    }
}
