stopthecap

high

# Non deposited amount is not returned to the user

## Summary
Non deposited amount is not returned to the user

## Vulnerability Detail
When providing liquidity to uniswap/fork of uni, users are sending a preliminary `amount1Desired` and `amount0Desired` of both tokens to the multipool contract.
 
https://github.com/sherlock-audit/2023-06-real-wagmi/blob/main/concentrator/contracts/Multipool.sol#L478-L481

When calling `_deposit` an optimal amount of `liquidity` is calculated according to the following formula:

https://github.com/sherlock-audit/2023-06-real-wagmi/blob/main/concentrator/contracts/Multipool.sol#L374-L379

The liquidity calculated by the multipool contract is passed as the mint param:

https://github.com/sherlock-audit/2023-06-real-wagmi/blob/main/concentrator/contracts/Multipool.sol#L385-L391

and then it gets calculated the exact amounts to send on the mint callback by uniswap, by checking the ticks:

```@solidity
 if (params.liquidityDelta != 0) {
            if (_slot0.tick < params.tickLower) {
                // current tick is below the passed range; liquidity can only become in range by crossing from left to
                // right, when we'll need _more_ token0 (it's becoming more valuable) so user must provide it
                amount0 = SqrtPriceMath.getAmount0Delta(
                    TickMath.getSqrtRatioAtTick(params.tickLower),
                    TickMath.getSqrtRatioAtTick(params.tickUpper),
                    params.liquidityDelta
                );
            } else if (_slot0.tick < params.tickUpper) {
                // current tick is inside the passed range
                uint128 liquidityBefore = liquidity; // SLOAD for gas optimization

                // write an oracle entry
                (slot0.observationIndex, slot0.observationCardinality) = observations.write(
                    _slot0.observationIndex,
                    _blockTimestamp(),
                    _slot0.tick,
                    liquidityBefore,
                    _slot0.observationCardinality,
                    _slot0.observationCardinalityNext
                );

                amount0 = SqrtPriceMath.getAmount0Delta(
                    _slot0.sqrtPriceX96,
                    TickMath.getSqrtRatioAtTick(params.tickUpper),
                    params.liquidityDelta
                );
                amount1 = SqrtPriceMath.getAmount1Delta(
                    TickMath.getSqrtRatioAtTick(params.tickLower),
                    _slot0.sqrtPriceX96,
                    params.liquidityDelta
                );

                liquidity = LiquidityMath.addDelta(liquidityBefore, params.liquidityDelta);
            } else {
                // current tick is above the passed range; liquidity can only become in range by crossing from right to
                // left, when we'll need _more_ token1 (it's becoming more valuable) so user must provide it
                amount1 = SqrtPriceMath.getAmount1Delta(
                    TickMath.getSqrtRatioAtTick(params.tickLower),
                    TickMath.getSqrtRatioAtTick(params.tickUpper),
                    params.liquidityDelta
                );
```

Therefore, the `amount1Desired` and `amount0Desired`  sent to multipool, are not the same amounts that uniswap will request to the multipool contract through the callback  `amount1Desired` and `amount0Desired`   and the actual amounts sent, are not reimbursed to the user, causing him to loss a portion of the funds he sent.

## Impact
Loss of funds for users depositing due to no reimbursement of liquidity not requested by uniswaps callback

## Code Snippet
https://github.com/sherlock-audit/2023-06-real-wagmi/blob/main/concentrator/contracts/Multipool.sol#L360-L416
https://github.com/sherlock-audit/2023-06-real-wagmi/blob/main/concentrator/contracts/Multipool.sol#L361-L362
https://github.com/sherlock-audit/2023-06-real-wagmi/blob/main/concentrator/contracts/Multipool.sol#L389
## Tool used

Manual Review

## Recommendation
Calculate the amount before and after sending the amounts to uniswap and compare them to what the user sent. The remaining, must be reimbursed, and here is the place you can substract any fee if needed too.