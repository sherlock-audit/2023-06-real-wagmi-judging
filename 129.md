lil.eth

medium

# Dangerous arbitrary external call can be used by the manager to steal funds from the users who have approved tokens to the vault contract

## Summary

Although Owner is trusted, there is a centralization mechanisms that needs be highlighted : 
For Users who approved multipool.sol contract to mint() directly, `manager`can rebalance with `token0` or `token1`'s address with well written payload.
Besides manager can also use this mechanism to sweep the amount in the balance and rug all users 

## Vulnerability Detail

`Multipool.sol#manageSwapTarget(address _target, bool _approved)` can be used by a manager to add swapTarget that can be used during rebalancing().
Then during `Multipool.sol#rebalanceAll()` approved swapTarget is called using : 
`(bool success, ) = params.swapTarget.call(params.swapData);`
So for users who approved the vault contract , `manager`can rebalance with `token0` or `token1`address as `params.swapTarget.call(params.swapData);` and transferFrom(victim,attacker,amount)`as payload to steal funds from the victim.

Using `transfer(attacker,amount)`as the payload , manager can also sweep the amounts in the balance to rug all users.

## Impact

Manager can rug all users.
As Manager and owner are trusted I let you mark this findings as high medium or out of scope if you want

## Code Snippet
https://github.com/sherlock-audit/2023-06-real-wagmi/blob/main/concentrator/contracts/Multipool.sol#L926
```solidity
    function manageSwapTarget(address _target, bool _approved) external onlyOwner {
        ErrLib.requirement(_target != address(0), ErrLib.ErrorCode.INVALID_ADDRESS);
        approvedTargets[_target] = _approved;
        emit SwapTargetApproved(_target, _approved);
    }
```
https://github.com/sherlock-audit/2023-06-real-wagmi/blob/main/concentrator/contracts/Multipool.sol#L926
```solidity
    /**
     * @dev This function closes all opened positions, swaps desired token to other(if needed) and opens new positions
     *      with new strategy settings
     * @param params Details for the swap
     * */
    function rebalanceAll(RebalanceParams calldata params) external nonReentrant {
        ....
        if (params.amountIn > 0) {
            _approveToken(params.zeroForOne ? token0 : token1, params.swapTarget, params.amountIn);
            (bool success, ) = params.swapTarget.call(params.swapData);
            ErrLib.requirement(success, ErrLib.ErrorCode.ERROR_SWAPPING_TOKENS);
        }
      ....
    }
```
## Tool used

Manual Review

## Recommendation
Consider blacklist token0 and token1 as `swapTarget` allowed when using `Multipool.sol#manageSwapTarget()`
