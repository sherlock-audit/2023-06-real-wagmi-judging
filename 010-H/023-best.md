twcctop

high

# Precision Loss in Calculating lowerTick and upperTick in _getTicksForPosition

## Summary

The function `_getTicksForPosition` in the code may encounter precision loss, resulting in `upperTick - lowerTick` not being equal to the specified `positionRange`. This deviation from the expected behavior violates the strategy setting.

## Vulnerability Detail

Code snippet: [Multipool.sol - Lines 261-262](https://github.com/sherlock-audit/2023-06-real-wagmi/blob/main/concentrator/contracts/Multipool.sol#L261-L262)

The following expressions are used to calculate the `lowerTick` and `upperTick` values:

makefileCopy code

`lowerTick = floorTick - (positionRange - tickSpacing) / 2; upperTick = floorTick + (positionRange + tickSpacing) / 2;`

According to the position limit, `upperTick - lowerTick` must be equal to `positionRange`. While this calculation works fine when `tickSpacing` is an even number, it encounters an issue when `tickSpacing` is an odd number. The Uniswap V3 documentation defines `tickSpacing` as a positive integer, with ticks initialized at multiples of this value.

For example, when:

makefileCopy code

`floorTick = 20; positionRange = 10; tickSpacing = 2;`

the calculations yield:

makefileCopy code

`lowerTick = 20 - (10 - 2) / 2 = 16; upperTick = 20 + (10 + 2) / 2 = 26;`

In this case, `upperTick - lowerTick` is equal to `positionRange`.

However, when:

makefileCopy code

`floorTick = 20; positionRange = 10; tickSpacing = 3;`

the calculations become:

makefileCopy code

`lowerTick = 20 - (10 - 3) / 2 = 17; upperTick = 20 + (10 + 3) / 2 = 26;`

In this case, `upperTick - lowerTick` is not equal to `positionRange`.

This discrepancy can result in `upperTick - lowerTick` not satisfying the strategy setting.

## Impact

The issue causes `upperTick - lowerTick` to deviate from the expected `positionRange`, which violates the strategy setting.

## Code Snippet

Code snippet: [Multipool.sol - Lines 261-262](https://github.com/sherlock-audit/2023-06-real-wagmi/blob/main/concentrator/contracts/Multipool.sol#L261-L262)

## Tool used

Manual Review

## Recommendation

To resolve the issue, modify the code as follows:

makefileCopy code

`lowerTick = floorTick - (positionRange - tickSpacing) / 2; upperTick = lowerTick + positionRange;`

This calculation ensures that `upperTick` is derived from `lowerTick` while maintaining the specified `positionRange`.