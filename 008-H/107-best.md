0xDjango

high

# Fees are lost if fee growth surpasses user's share value

## Summary
In `Dispatcher.sol`, when a user withdraws LP, the fees that are owed to them is subtracted from their current LP balance. In the case where the position’s earned fees outweigh the position’s current shares, claiming fees will cause a revert due to underflow.

If trading volume within the UniV3 position ticks are substantial, it can be expected that fees can outweigh initial value within a reasonable amount of time (1 to 2 years).

## Vulnerability Detail
Quite simply, since the fees are subtracted from the user's LP balance, if the fees amount to more than the initial value of the deposit, fee withdrawal will revert due to underflow.

In order to withdraw the original LP value, the user must withdraw while declining receiving the fees.

## Impact
- Loss of earned fees

## Code Snippet
https://github.com/sherlock-audit/2023-06-real-wagmi/blob/82a234a5c2c1fc1921c63265a9349b71d84675c4/concentrator/contracts/Dispatcher.sol#L236
```solidity
    function withdraw(uint256 pid, uint256 amount, uint256 deviationBP) external checkPid(pid) {
        ...

        } else if (amount < user.shares) {
            uint256 lpAmount;
            {
                (uint256 fee0, uint256 fee1) = _calcFees(feesGrow, user);
                lpAmount = _estimateWithdrawalLp(reserve0, reserve1, _totalSupply, fee0, fee1);
            }
            user.shares -= lpAmount;
```

## Tool used
Manual Review

## Recommendation
Do not subtract fees from LP balance.
