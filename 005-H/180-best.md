minhtrng

high

# Incorrect usage of slippage protection params

## Summary

The parameters passed as slippage protection are used incorrectly, causing users to overpay.

## Vulnerability Detail

The function `deposit` receives the parameters `amount0Min` and `amount1Min` which are meant to be for slippage protection:

```js
@param amount0Min The minimum amount of token0 required to be deposited.
@param amount1Min The minimum amount of token1 required to be deposited.
```

These parameters are used within `_optimizeAmounts` to recalculate the values for `amount0Desired/amount1Desired`:

```js
//in deposit
(amount0Desired, amount1Desired) = _optimizeAmounts(
    amount0Desired,
    amount1Desired,
    amount0Min,
    amount1Min,
    reserve0,
    reserve1
);

// in _optimizeAmounts
if (reserve0 == 0 && reserve1 == 0) {
    (amount0, amount1) = (amount0Desired, amount1Desired);
} else {
    uint256 amount1Optimal = _quote(amount0Desired, reserve0, reserve1);
    if (amount1Optimal <= amount1Desired) {
        ErrLib.requirement(
            amount1Optimal >= amount1Min,
            ErrLib.ErrorCode.INSUFFICIENT_1_AMOUNT
        );
        (amount0, amount1) = (amount0Desired, amount1Optimal);
    } else {
        ...
```

`_quote` uses a UniV2 sort of calculation to calculate the amountOut for an input amount:

```js
//WARDEN-NOTE: this is the quote function as found in UniswapV2Library.sol
function _quote(
    uint256 amountA,
    uint256 reserveA,
    uint256 reserveB
) private pure returns (uint256 amountB) {
    ErrLib.requirement(amountA > 0, ErrLib.ErrorCode.INSUFFICIENT_AMOUNT);
    ErrLib.requirement(reserveA > 0 && reserveB > 0, ErrLib.ErrorCode.INSUFFICIENT_LIQUIDITY);
    amountB = (amountA * reserveB) / reserveA;
}
```

However, using the results of this calculation as the "optimal amount" is false, as it does not represent the actual amount required when minting positions across the different v3 pools.

## Impact

Slippage protection does not work as intended

## Code Snippet

https://github.com/sherlock-audit/2023-06-real-wagmi/blob/main/concentrator/contracts/Multipool.sol#L459-L466

## Tool used

Manual Review

## Recommendation

The actual slippage protection as can be found in the official UniV3-periphery `LiquidityManagement.addLiquidity` should use the return values of `UniswapV3Pool.mint` and check against the slippage input params like this:

```js
(amount0, amount1) = pool.mint(
    params.recipient,
    params.tickLower,
    params.tickUpper,
    liquidity,
    abi.encode(MintCallbackData({poolKey: poolKey, payer: msg.sender}))
);

require(amount0 >= params.amount0Min && amount1 >= params.amount1Min, 'Price slippage check');
```