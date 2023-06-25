stopthecap

high

# Wrong calculation of `tickCumulatives` due to hardcoded pool fees

## Summary
Wrong calculation of `tickCumulatives` due to hardcoded pool fees

## Vulnerability Detail
Real Wagmi is using a hardcoded `500` fee to calculate the `amountOut` to check for slippage and revert if it was to high, or got less funds back than expected. 

```@solidity
 IUniswapV3Pool(underlyingTrustedPools[500].poolAddress)
```

There are several problems with the hardcoding of the `500` as the fee.

- Not all tokens have `500` fee pools
- The swapping takes place in pools that don't have a `500` fee
- The `500` pool fee is not the optimal to fetch the `tickCumulatives` due to low volume

Specially as they are deploying in so many secondary chains like Kava, this will be a big problem pretty much in every transaction over there.

If any of those scenarios is given, `tickCumulatives`  will be incorrectly calculated and it will set an incorrect slippage return.

## Impact
Incorrect slippage calculation will increase the risk of `rebalanceAll()` rebalance getting rekt.

## Code Snippet
https://github.com/sherlock-audit/2023-06-real-wagmi/blob/main/concentrator/contracts/Multipool.sol#L816-L838
https://github.com/sherlock-audit/2023-06-real-wagmi/blob/main/concentrator/contracts/Multipool.sol#L823
## Tool used

Manual Review

## Recommendation
Consider allowing the fees as an input and consider not even picking low TVL pools with no transations