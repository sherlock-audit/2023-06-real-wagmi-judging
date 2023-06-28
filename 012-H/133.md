lil.eth

medium

# Rounding Error in the _estimateWithdrawalLp Function of Liquidity Withdrawal Estimation

## Summary

The `_estimateWithdrawalLp` function, used for estimating the amount of liquidity shares needed to be withdrawn to claim fees in a dual-token liquidity pool, might be subject to rounding errors due to integer division. This can result in the calculation being slightly off, impacting the accuracy of the estimated shares to withdraw.

## Vulnerability Detail
The `_estimateWithdrawalLp` function takes in the following parameters:

`reserve0`: Total reserve of token0.
`reserve1`: Total reserve of token1.
`_totalSupply`: Total number of shares.
`amount0`: Amount user wants to claim of token0.
`amount1`: Amount user wants to claim of token1.
The function calculates the estimated share amount to be withdrawn as:

`shareAmount = ((amount0 * _totalSupply) / reserve0 + (amount1 * _totalSupply) / reserve1) / 2;`

This calculation includes two divisions:

1. `(amount0 * _totalSupply) / reserve0`
2. `(amount1 * _totalSupply) / reserve1`

Both of these divisions are integer divisions, meaning that if the numerator is not perfectly divisible by the denominator, the fraction is truncated. This truncation introduces a rounding error. Additionally, dividing their sum by 2 can further aggregate the error.
### POC 
```solidity
uint256 reserve0 = 1500;    // Total reserve of token0
uint256 reserve1 = 1200;    // Total reserve of token1
uint256 _totalSupply = 500; // Total supply of LP tokens
uint256 amount0 = 100;      // Amount user wants to claim of token0
uint256 amount1 = 80;       // Amount user wants to claim of token1
```
=> `shareAmount = (33.33333333 + 33.33333333) / 2;`
`shareAmount = 33;`
If these rounding errors accumulate over many transactions, it can result in a noticeable discrepancy. To mitigate this, some developers implement error correction strategies, while others simply accept the small loss in precision as a trade-off for the simplicity and security of using integer arithmetic.

## Impact

In certain cases, this rounding error could cause the calculated `shareAmount` to be slightly higher or lower than the actual value. This might lead to imprecise liquidity withdrawals, which could affect the balances and, in turn, the state of the liquidity pool.

## Code Snippet
https://github.com/sherlock-audit/2023-06-real-wagmi/blob/main/concentrator/contracts/Dispatcher.sol#L140
```solidity
    function _estimateWithdrawalLp(
        uint256 reserve0,
        uint256 reserve1,
        uint256 _totalSupply,
        uint256 amount0,
        uint256 amount1
    ) private pure returns (uint256 shareAmount) {
        shareAmount =
            ((amount0 * _totalSupply) / reserve0 + (amount1 * _totalSupply) / reserve1) /
            2;
    }
```
## Tool used

Manual Review

## Recommendation

Use FullMath library to scale up the numerator by 1e18
