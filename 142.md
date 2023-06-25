duc

high

# The `_estimateWithdrawalLp` function might return a very large value, result in users losing significant incentives or being unable to withdraw from the Dispatcher contract

## Summary
The `_estimateWithdrawalLp` function might return a very large value, result in users losing significant incentives or being unable to withdraw from the Dispatcher contract
## Vulnerability Detail
In Dispatcher contract, `_estimateWithdrawalLp` function returns the value of shares amount based on the average of ratios `amount0 / reserve0` and `amount1 / reserve1`.
```solidity=
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
From `Dispatcher.withdraw` and `Dispatcher.deposit` function, amount0 and amount1 will be the accumulated fees of users
```solidity=
uint256 lpAmount;
{
    (uint256 fee0, uint256 fee1) = _calcFees(feesGrow, user);
    lpAmount = _estimateWithdrawalLp(reserve0, reserve1, _totalSupply, fee0, fee1);
}
user.shares -= lpAmount;
_withdrawFee(pool, lpAmount, reserve0, reserve1, _totalSupply, deviationBP);
```
However, it is important to note that the values of reserve0 and reserve1 can fluctuate significantly. This is because the positions of the Multipool in UniSwapV3 pools (concentrated) are unstable on-chain, and they can change substantially as the state of the pools changes. As a result, the `_estimateWithdrawalLp` function might return a large value even for a small fee amount. This could potentially lead to reverting due to underflow in the deposit function (in cases where `lpAmount > user.shares`), or it could result in withdrawing a larger amount of Multipool LP than initially expected.

Scenario:
1. Total supply of Multipool is 1e18, and Alice has 1e16  (1%) LP amounts which deposited into Dispatcher contract.
2. Alice accrued fees = 200 USDC and 100 USDT
3. The reserves of Multipool are 100,000 USDC and 100,000 USDT, `_estimateWithdrawalLp` of Alice fees will be `(0.2% + 0.1%) / 2 * totalSupply` = `0.15% * totalSupply` = 1.5e15 LP amounts
4. However, in some cases, UniSwapV3 pools may experience fluctuations, reserves of Multipool are 10,000 USDC and 190,000 USDT, `_estimateWithdrawalLp` of Alice fees will be `(2% + 0.052%) / 2 * totalSupply` = `1.026% * totalSupply` = 1.026e16 LP amounts
This result is greater than LP amounts of Alice (1e16), leading to reverting by underflow in deposit/withdraw function of Dispatcher contract.
## Impact
Users may face 2 potential issues when interacting with the Dispatcher contract. 
1. They might be unable to deposit/withdraw
2. Secondly, users could potentially lose significant incentives when depositing or withdrawing due to unexpected withdrawals of LP amounts for their fees.
## Code Snippet
https://github.com/sherlock-audit/2023-06-real-wagmi/blob/main/concentrator/contracts/Dispatcher.sol#L140-L150
## Tool used
Manual review

## Recommendation
Shouldn't use the average ratio for calculation in`_estimateWithdrawalLp` function