shealtielanz

medium

# Incorrect ratioX196 calculated due to casting.

## Summary
the ratioX192 is calculated from the sqrtPriceX96^2 however only one is casted to uint.
## Vulnerability Detail
The issue is in the multipool getAmountOut function.

        uint160 sqrtPriceX96 = TickMath.getSqrtRatioAtTick(avarageTick);
        if (sqrtPriceX96 <= type(uint128).max) {
            uint256 ratioX192 = uint256(sqrtPriceX96) * sqrtPriceX96;
            swappedOut = zeroForOne
                ? FullMath.mulDiv(ratioX192, amountIn, 1 << 192)
                : FullMath.mulDiv(1 << 192, amountIn, ratioX192);
        } else {
            uint256 ratioX128 = FullMath.mulDiv(sqrtPriceX96, sqrtPriceX96, 1 << 64);
            swappedOut = zeroForOne
                ? FullMath.mulDiv(ratioX128, amountIn, 1 << 128)
                : FullMath.mulDiv(1 << 128, amountIn, ratioX128);
        }
here only one sqrtPriceX96 is casted down to uint256 causing truncation that will cause inaccuracies when bit shifting the ratioX192
## Impact
The is the ratioX192 is incorrect this lead to wrong prices and also incorrect amountOut calculated causing loss of funds to users
## Code Snippet
https://github.com/sherlock-audit/2023-06-real-wagmi/blob/main/concentrator/contracts/Multipool.sol#L826C1-L837C10
## Tool used

Manual Review

## Recommendation
Use the safeCast library and do appropriate casting to the values of sqrtPriceX96.