oxchryston

medium

# Downcasting may overflow silently.

## Summary
Overflow may occur due to `downcasting` from `uint256` to `uint128` in the `withdraw` function when calculating the `liquidityToWithdraw`.
## Vulnerability Detail
In the `withdraw` function, the `liquidityToWithdraw` was calculated and downcasted from ùint256` to ùint128`. This action can fail silently as `solidity` does not check if it is safe to cast an integer to a smaller one.
```solidity
   function _withdraw(
        uint256 lpAmount,
        uint256 _totalSupply
    ) private returns (uint256 withdrawnAmount0, uint256 withdrawnAmount1) {
        assert(_totalSupply > 0);
        PositionInfo memory position;
        uint256 posNum = multiPosition.length;
        uint256 fee0;
        uint256 fee1;
        for (uint256 i = 0; i < posNum; ) {
            position = multiPosition[i];

            {
                (uint128 liquidity, , , , ) = IUniswapV3Pool(position.poolAddress).positions(
                    position.positionKey
                );

                uint128 liquidityToWithdraw = uint128(
                    (uint256(liquidity) * lpAmount) / _totalSupply
                );
              // more code...
```
## Impact
`liquidityToWithdraw` can overflow leading to users withdrawing less liquidity than they intended leading to `dos`.
## Code Snippet
https://github.com/sherlock-audit/2023-06-real-wagmi/blob/main/concentrator/contracts/Multipool.sol#L488C2-L508C1
## Tool used

Manual Review

## Recommendation
Add checks or use `safecast` for casting integers.