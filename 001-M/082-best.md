BugBusters

high

# Possible precision loss in `_checkpositionsRange` function

## Summary
The `_checkpositionsRange` function contains a potential precision loss issue. The problem arises from the expression ((_range / 2) % _tickSpacing != 0).

## Vulnerability Detail
The vulnerability lies in the calculation of `(_range / 2) % _tickSpacing`. The code assumes that _range and _tickSpacing are both int24 variables, representing signed 24-bit integers. However, when  `_range` is 9 and `_tickSpacing` is, for example, 3, the division operation (_range / 2) will truncate the fractional part, resulting in 4 instead of 4.5. Subsequently, the modulo operation (4 % _tickSpacing) will evaluate to 1. This can lead to incorrect comparisons and unexpected behavior.

## Impact
It can potentially lead to incorrect validation and can also affect the correctness of the positions range check, potentially allowing invalid positions to be considered valid

## Code Snippet
```solidity
function _checkpositionsRange(
        int24 _range,
        int24 _tickSpacing,
        int24 tickSpacingOffset
    ) private pure {
        ErrLib.requirement(
            (_range > _tickSpacing) &&
                (_range % _tickSpacing == 0) &&
                (((_range / 2) % _tickSpacing != 0) || tickSpacingOffset != 0),
            ErrLib.ErrorCode.INVALID_POSITIONS_RANGE 
        );
    }
```
https://github.com/sherlock-audit/2023-06-real-wagmi/blob/82a234a5c2c1fc1921c63265a9349b71d84675c4/concentrator/contracts/MultiStrategy.sol#L93-L104
## Tool used

Manual Review

## Recommendation
