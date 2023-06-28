0xAsen

medium

# uint24 used for a fee - the maximum value is too small

## Summary
In the Multipool contract, we declare the fees as uint24 and map them to their corresponding pool:
```solidity
uint24[] public fees
//      fee =>poolAddress
mapping(uint24 => UnderlyingPool) public underlyingTrustedPools
``` 
However, the maximum value of uint24 might be too small.
## Vulnerability Detail
The uint24 max value is 16,777,215. However, this might turn out too small given that the pool will work with all kinds of tokens, some with at least 1e18 decimal places.

For perspective, (16,777,215/1e18)*100 = ~0.00000000167773%

For example, USDT on BSC has 18 decimals, and the maximum fee you'll be able to use is ~0.00000000167773% of 1 USDT. 
## Impact
The protocol won't be able to collect an appropriate amount of fees, especially for tokens with many decimals.
## Code Snippet
https://github.com/sherlock-audit/2023-06-real-wagmi/blob/main/concentrator/contracts/Multipool.sol#L68
## Tool used

Manual Review

## Recommendation
Use a bigger size variable, uint64 for example. 