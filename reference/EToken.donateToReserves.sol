// SPDX-License-Identifier: GPL-2.0-or-later
//
// ABRIDGED EXCERPT of real deployed code -- euler-xyz/euler-contracts,
// contracts/modules/EToken.sol (pre-hack state, March 2023).
//
// Reproduced here ONLY as the human-readable scan target for Litmus case004.
// It is intentionally placed under reference/ so Foundry does NOT compile it
// (it depends on Euler's module/proxy framework). The vulnerability is proven
// against the LIVE mainnet bytecode in
//   ../test/case004_euler_donate_insolvency/EulerDonatePoC.t.sol
//
// THE BUG: donateToReserves() reduces the caller's eToken (collateral) balance
// but -- unlike withdraw / transfer / mint / burn, which all end with
// checkLiquidity(account) -- never performs the post-operation solvency check.
// An account holding debt can therefore donate all of its collateral and become
// insolvent with NO revert, minting bad debt. This is the root cause of the
// ~$197M loss; the attacker then self-liquidated the insolvent position.

pragma solidity ^0.8.0;

contract EToken_excerpt {
    // ---- a SIBLING that does it right: withdraw ends with the solvency check ----
    function withdraw(uint256 subAccountId, uint256 amount) external /* nonReentrant */ {
        // ... CALLER(); getSubAccount(); loadAssetCache(); decode amount ...
        // ... assetStorage.users[account].balance -= amount;   (collateral reduced)
        // ... pushTokens(underlying, msgSender, amount);
        // ... logations / interest accrual ...
        // checkLiquidity(account);                 // <-- SOLVENCY ENFORCED HERE
    }

    // ---- the VULNERABLE function: same collateral reduction, NO checkLiquidity ----
    function donateToReserves(uint256 subAccountId, uint256 amount) external /* nonReentrant */ {
        // (address underlying, AssetStorage storage assetStorage, , address msgSender) = CALLER();
        // address account = getSubAccount(msgSender, subAccountId);
        // AssetCache memory assetCache = loadAssetCache(underlying, assetStorage);

        // uint origBalance = assetStorage.users[account].balance;
        // uint newBalance;
        // if (amount == type(uint).max) { amount = origBalance; newBalance = 0; }
        // else { require(origBalance >= amount, "e/insufficient-balance"); newBalance = origBalance - amount; }

        // assetStorage.users[account].balance   = encodeAmount(newBalance);              // collateral burned
        // assetStorage.reserveBalance = assetCache.reserveBalance
        //                              = encodeSmallAmount(assetCache.reserveBalance + amount);

        // emit RequestDonate(account, amount);
        //
        // >>> NO checkLiquidity(account) -- the single omission that minted ~$197M of bad debt <<<
    }
}
