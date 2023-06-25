lil.eth

medium

# Rounding Errors in the _getTicksForPosition()

## Summary
The `_getTicksForPosition()` function of Uniswap V3 smart contracts may be subject to rounding errors. The function is used when adding range to add liquidity and could prevent initialization of the strategy or providing liquidity to bad ranges

## Vulnerability Detail
The `_getTicksForPositio()` function calculates the range in which liquidity will be provided by taking into account parameters such as the current tick, the desired range of position in terms of ticks, an offset to adjust the placement of the liquidity range, and the minimum difference in ticks between liquidity bounds. The function performs integer divisions during these calculations, which can lead to rounding errors.

The key code line is `int24 floorTick = (tick / tickSpacing) * tickSpacing;,` where the calculated floor tick might differ from the actual due to the integer division rounding. Subsequent calculations like `lowerTick = floorTick - (positionRange - tickSpacing) / 2; and upperTick = floorTick + (positionRange + tickSpacing) / 2;` also introduce potential rounding errors.


 If a rounding error in `_getTicksForPosition()` causes lowerTick or upperTick to not align with the tick spacing, _checkTicks() will revert.
### POC
```solidity
// We want to provide liquidity around the current tick, which is 1200
int24 tick = 1200;
// We want our position to span 30 ticks
int24 positionRange = 30;
// We have no tickSpacingOffset
int24 tickSpacingOffset = 0;
// The tick spacing for this pool is 10
int24 tickSpacing = 10;
```

```solidity
// Running _getTicksForPosition() with these parameters:
(lowerTick, upperTick) = _getTicksForPosition(tick, positionRange, tickSpacingOffset, tickSpacing);

// The floorTick is the largest tick that aligns with tickSpacing
int24 floorTick = (tick / tickSpacing) * tickSpacing;  // = (1200 / 10) * 10 = 1200

// As tickSpacingOffset is 0, liquidity is placed around the floorTick
lowerTick = floorTick - (positionRange - tickSpacing) / 2; // = 1200 - (30 - 10) / 2 = 1190
upperTick = floorTick + (positionRange + tickSpacing) / 2; // = 1200 + (30 + 10) / 2 = 1210

// When we check these ticks:
_checkTicks(lowerTick, upperTick, tickSpacing);

// lowerTick % tickSpacing = 1190 % 10 = 0, which is fine
// upperTick % tickSpacing = 1210 % 10 = 0, which is fine

// Now let's change the positionRange to 31, which will lead to a rounding error:
positionRange = 31;

(lowerTick, upperTick) = _getTicksForPosition(tick, positionRange, tickSpacingOffset, tickSpacing);

// lowerTick = floorTick - (positionRange - tickSpacing) / 2; = 1200 - (31 - 10) / 2 = 1189.5
// upperTick = floorTick + (positionRange + tickSpacing) / 2; = 1200 + (31 + 10) / 2 = 1210.5
// But as Solidity doesn't support decimals, these get rounded down to 1189 and 1210

// When we check these ticks:
_checkTicks(lowerTick, upperTick, tickSpacing);

// lowerTick % tickSpacing = 1189 % 10 = 9, which fails the check in _checkTicks(), causing it to revert
// upperTick % tickSpacing = 1210 % 10 = 0, which is fine
```

## Impact

These rounding errors can lead to discrepancies in the calculated lower and upper ticks that define the liquidity range. As a result, liquidity might not be provided in the intended range. Or even revert all the transactions to add liquidity ranges

## Code Snippet
https://github.com/sherlock-audit/2023-06-real-wagmi/blob/main/concentrator/contracts/Multipool.sol#L253
```solidity
function _getTicksForPosition(
        int24 tick,
        int24 positionRange,
        int24 tickSpacingOffset,
        int24 tickSpacing
    ) private pure returns (int24 lowerTick, int24 upperTick) {
        int24 floorTick = (tick / tickSpacing) * tickSpacing;
        if (tickSpacingOffset == 0) {
            lowerTick = floorTick - (positionRange - tickSpacing) / 2;
            upperTick = floorTick + (positionRange + tickSpacing) / 2;
        } else if (tickSpacingOffset > 0) {
            lowerTick = floorTick + tickSpacing * tickSpacingOffset;
            upperTick = lowerTick + positionRange;
        } else {
            upperTick = floorTick + tickSpacing * tickSpacingOffset;
            lowerTick = upperTick - positionRange;
        }
    }
```

## Tool used

Manual Review

## Recommendation

1. Round the result of your division operation to the nearest multiple of tickSpacing: If lowerTick and upperTick values must be divisible by tickSpacing, then you could manually round the result of your division operation to ensure it's a multiple of tickSpacing. This could be achieved by adding half of tickSpacing before the division and subtracting the remainder after the division:
```solidity
lowerTick = (floorTick * 2 - positionRange + tickSpacing) / (2 * tickSpacing) * tickSpacing;
upperTick = (floorTick * 2 + positionRange + tickSpacing) / (2 * tickSpacing) * tickSpacing;
```
3. Add explicit checks and adjustments: If after all your calculations, the lowerTick and upperTick are still not divisible by tickSpacing, you could add a check and an adjustment to make them divisible:
```solidity
if (lowerTick % tickSpacing != 0)
    lowerTick -= lowerTick % tickSpacing;
if (upperTick % tickSpacing != 0)
    upperTick -= upperTick % tickSpacing;
```