stopthecap

medium

# Incorrect order when calling `getAmountOut` calculates incorrectly the amount swapped

## Summary
Incorrect order when calling `getAmountOut` calculates incorrectly the amount swapped

## Vulnerability Detail
When `rebalancingAll()` a certain `amountIn` is sent to be swapped in the aggregator that real wagmi chooses.

```@solidity
 _approveToken(params.zeroForOne ? token0 : token1, params.swapTarget, params.amountIn);
            (bool success, ) = params.swapTarget.call(params.swapData);
```

after the swap, the do check both balances of both tokens to see how much of each token as been sent and got back:

```@solidity
uint reserve0 = IERC20(token0).balanceOf(address(this));
        uint reserve1 = IERC20(token1).balanceOf(address(this));
```

They do make the exact calculation to determine the exact amount swapped: 

```@solidity
 uint256 amountOut = params.zeroForOne
            ? reserve1 - reserve1Before
            : reserve0 - reserve0Before;
```

and for the `amountOut` they check the `getAmountOut()` function that does return the expected amount out that you would get at  that exact time for the `amountIn` sent:   

```@solidity
 uint256 swappedOut = getAmountOut(params.zeroForOne, amountIn);
        if (amountOut < swappedOut) {
            ErrLib.requirement(
                (swappedOut * maxTwapDeviation) / MAX_WEIGHT_UINT256 >= swappedOut - amountOut,
                ErrLib.ErrorCode.PRICE_SLIPPAGE_CHECK
            );
```

The problem is that `getAmountOut` has already been updated after swapping on the wagmi's desired pool, having a divergence in price with the actual `amount` of the swap they did, moving the `reserves` of each token and its `amountsOut`

Therefore the calculation of the `if (amountOut < swappedOut) {` will be wrong, and depending where the reserves and the calculation will move, either the function will fail, or you will accept more slippage, potentially losing tokens, than the intended.

## Impact
Depending where the reserves and the calculation will move, either the function will fail, or you will accept more slippage, potentially losing tokens, than the intended.

## Code Snippet
https://github.com/sherlock-audit/2023-06-real-wagmi/blob/main/concentrator/contracts/Multipool.sol#L845-L881

https://github.com/sherlock-audit/2023-06-real-wagmi/blob/main/concentrator/contracts/Multipool.sol#L875
## Tool used

Manual Review

## Recommendation
Move the `getAmountOut` call to before the swap happened, not after