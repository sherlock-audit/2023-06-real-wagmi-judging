talfao

medium

# Out of gas of rebalance function, if many strategies exist.

## Summary
Out of gas of rebalance function, if many strategies exist when calling  _initializeStrategy() method inside it.
## Vulnerability Detail
There is a possibility of failure of rebalanceAll() method when it calls _initializeStrategy() due to the not restricted number of strategies which can be inserted into the Currentstrategy in MultiStrategy contract via setStrategy method.
## Impact
The out of gas could lead to loss of funds for the manager (caller of rebalanceAll method) and restrict a manager from successfully finishing the rebalance method. - leading to the restriction of maintaining the investment strategies of the protocol.
## Code Snippet
```Solidity
 function _initializeStrategy() private returns (Slot0Data[] memory) {
 uint256 positionsNum = strategy.strategySize(); // @audit-issue - the Size is not restricted
        ErrLib.requirement(positionsNum > 0, ErrLib.ErrorCode.STRATEGY_DOES_NOT_EXIST);
        delete multiPosition;
        PositionInfo memory position;
        int24 upperTick;
        int24 lowerTick;
        Slot0Data[] memory slots = new Slot0Data[](positionsNum);

        for (uint256 i = 0; i < positionsNum; ) {
            IMultiStrategy.Strategy memory sPosition = strategy.getStrategyAt(i);
            UnderlyingPool memory uPool = underlyingTrustedPools[sPosition.poolFeeAmt];
            ....
    
```

## Tool used

Manual Review

## Recommendation
I recommend putting some control over a number of strategies at the setStrategy function; https://github.com/sherlock-audit/2023-06-real-wagmi/blob/82a234a5c2c1fc1921c63265a9349b71d84675c4/concentrator/contracts/MultiStrategy.sol#L57C5-L61C61
Like:
```Solidity
if (_currentStrategy.length > 20){
revert ....;
}
```