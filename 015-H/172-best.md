Avci

high

# The estimated remove amount for lp token amount to remove after withdraw is based on total supply can be manipulated and its possible to even withdraw more than share

## Summary
The estimated remove amount for the lp token amount to remove after withdrawal is based on the total supply can be manipulated and it's possible to even withdraw more than the share
## Vulnerability Detail
when the logic of the   function   _estimateWithdrawalLp : depends on total supply then its possible to manipulate the _estimateWithdrawalLp  return which calculates the 
```solidity
 shareAmount =
            ((amount0 * _totalSupply) / reserve0 + (amount1 * _totalSupply) / reserve1) /
            2;
```
and because this function is called in other functions 
```solidity 
 function estimateClaim(
        uint256 pid,
        address userAddress
    )
        external
        view
        checkPid(pid)
        returns (uint256 lpAmountRemoved, uint256 amount0, uint256 amount1)
    {
        PoolInfo memory pool = poolInfo[pid];
        UserInfo memory user = userInfo[pid][userAddress];
        if (user.shares > 0) {
            IMultipool.FeeGrowth memory feesGrow = IMultipool(pool.multipool)
                .feesGrowthInsideLastX128();
            (uint256 fee0, uint256 fee1) = _calcFees(feesGrow, user);
            (
                uint256 reserve0,
                uint256 reserve1,
                uint256 pendingFee0,
                uint256 pendingFee1
            ) = IMultipool(pool.multipool).getReserves();
            uint256 _totalSupply = IERC20(pool.multipool).totalSupply();
            fee0 += (pendingFee0 * user.shares) / _totalSupply;
            fee1 += (pendingFee1 * user.shares) / _totalSupply;
            lpAmountRemoved = _estimateWithdrawalLp(reserve0, reserve1, _totalSupply, fee0, fee1);
            amount0 = (reserve0 * lpAmountRemoved) / _totalSupply;
            amount1 = (reserve1 * lpAmountRemoved) / _totalSupply;
        }
    }
```
bad actors cam manipulate lpAmountRemoved  easily 
## Impact
 its possible to even withdraw more than share/ create unwanted results 
## Code Snippet
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
https://github.com/sherlock-audit/2023-06-real-wagmi/blob/main/concentrator/contracts/Dispatcher.sol#L139-L150
## Tool used

Manual Review

## Recommendation
- consider redesigning the logic to a way that logic does not rely on supply in the way that it can get manipulated