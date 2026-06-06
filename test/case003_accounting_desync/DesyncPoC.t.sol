// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import {Test} from "forge-std/Test.sol";
import {FeeToken} from "../../src/case003_accounting_desync/FeeToken.sol";
import {CachedVault} from "../../src/case003_accounting_desync/CachedVault.sol";

/// @notice Runnable proof for case003 -- cached-accounting desync.
///         A PASSING test means the cache overstated real assets and the final
///         withdrawer was bricked (their withdrawal reverts for lack of funds).
contract DesyncPoC is Test {
    FeeToken internal token;
    CachedVault internal vault;
    address internal alice;
    address internal bob;

    function setUp() public {
        token = new FeeToken();
        vault = new CachedVault(token);
        alice = makeAddr("alice");
        bob = makeAddr("bob");
        token.mint(alice, 100e18);
        token.mint(bob, 100e18);
    }

    function test_feeOnTransferDesyncBricksLastWithdrawer() public {
        vm.startPrank(alice);
        token.approve(address(vault), type(uint256).max);
        vault.deposit(100e18);
        vm.stopPrank();

        vm.startPrank(bob);
        token.approve(address(vault), type(uint256).max);
        vault.deposit(100e18);
        vm.stopPrank();

        // Cache claims 200 but the vault really holds 198 (1% fee on each deposit).
        assertEq(vault.cachedTotal(), 200e18, "cache should overstate");
        assertEq(token.balanceOf(address(vault)), 198e18, "real balance is short");

        // Alice exits first, paid in full against the inflated cache.
        vm.prank(alice);
        vault.withdraw();
        assertEq(token.balanceOf(address(vault)), 98e18, "first withdrawer pushes the shortfall onto the last");

        // Bob is now bricked: owed 100, only 98 remains.
        vm.prank(bob);
        vm.expectRevert();
        vault.withdraw();

        emit log_string("last withdrawer bricked by cache/real desync (owed 100, only 98 left)");
    }
}
