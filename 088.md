duc

high

# Reserves calculation of Multipool contract is incorrect

## Summary
The `_getReserves` function in the Multipool contract incorrectly accumulates all accrued fees from positions (which have not been collected yet), without deducting the protocol fees. As a result, the returned reserves are higher than the actual value, causing users to receive less LP amounts than they should.
## Vulnerability Detail
In the `_getReserves` function, the protocol fee ratio is used to deduct and accumulate the pending fees (unaccrued fees) from the positions in UniSwapV3 pools.
```solidity=
///https://github.com/sherlock-audit/2023-06-real-wagmi/blob/main/concentrator/contracts/Multipool.sol#L761-L767
// take away protocol fee
uint256 feeGrowthWeight = MAX_WEIGHT_UINT256 - protocolFeeWeight;
pendingFee0 = (pendingFee0 * feeGrowthWeight) / MAX_WEIGHT_UINT256;
pendingFee1 = (pendingFee1 * feeGrowthWeight) / MAX_WEIGHT_UINT256;

reserve0 += pendingFee0;
reserve1 += pendingFee1;
```
However, the accrued fees (accrued from UniV3 pools but not collected) of the positions are not deducted like that, leading to accumulate reserves incorrectly
```solidity=
///https://github.com/sherlock-audit/2023-06-real-wagmi/blob/main/concentrator/contracts/Multipool.sol#L710-L720
uint128 tokensOwed0;
uint128 tokensOwed1;
(
    liquidity,
    feeGrowthInside0LastX128,
    feeGrowthInside1LastX128,
    tokensOwed0,
    tokensOwed1
) = IUniswapV3Pool(position.poolAddress).positions(position.positionKey);
reserve0 += tokensOwed0;
reserve1 += tokensOwed1;
```
When depositing or withdrawing, the `_upFeesGrowth` function is triggered, which calculates and transfers the protocol fees to the owner. This results in the actual collected fees of the Multipool contract being less than the calculation performed in the `_getReserve` function.
## Impact
Because the incorrect higher reserve amounts, users will receive less LP amounts than they should.
## Code Snippet
https://github.com/sherlock-audit/2023-06-real-wagmi/blob/main/concentrator/contracts/Multipool.sol#L710-L720
## Tool used
Manual review

## Recommendation
Should deduct the accrued fees by protocol fee ratio in `_getReserve` function, as the following:
```solidity=
uint256 feeGrowthWeight = MAX_WEIGHT_UINT256 - protocolFeeWeight;
tokensOwed0 = (tokensOwed0 * feeGrowthWeight) / MAX_WEIGHT_UINT256;
tokensOwed1 = (tokensOwed1 * feeGrowthWeight) / MAX_WEIGHT_UINT256;

reserve0 += tokensOwed0;
reserve1 += tokensOwed1;
```