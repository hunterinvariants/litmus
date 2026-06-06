// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// @title LPVault
/// @notice ETH vault whose share price is read by integrators as an oracle.
///         Ground-truth vulnerability: read-only reentrancy. withdraw() makes the
///         ETH transfer BEFORE updating share accounting, so pricePerShare()
///         returns a manipulated value to any contract called back during the
///         transfer. See bench/case002.json.
contract LPVault {
    mapping(address => uint256) public shares;
    uint256 public totalShares;

    function deposit() external payable {
        shares[msg.sender] += msg.value;
        totalShares += msg.value;
    }

    /// @notice Assets-per-share, scaled to 1e18. Integrators read this as a price.
    function pricePerShare() public view returns (uint256) {
        if (totalShares == 0) return 1e18;
        return address(this).balance * 1e18 / totalShares;
    }

    /// @dev VULNERABLE: violates checks-effects-interactions. The external ETH
    ///      transfer happens BEFORE shares/totalShares are decremented, so during
    ///      the recipient's callback the balance is already reduced while
    ///      totalShares is not -- pricePerShare() reads far below its true value.
    function withdraw(uint256 amt) external {
        uint256 payout = amt * address(this).balance / totalShares;
        (bool ok, ) = msg.sender.call{value: payout}("");
        require(ok, "transfer failed");
        shares[msg.sender] -= amt;
        totalShares -= amt;
    }
}
