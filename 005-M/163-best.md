Avci

high

# The deposit - withdraw - trade transaction lack of expiration timestamp check (DeadLine check)

## Summary
The deposit - withdraw - trade transaction lack of expiration timestamp check (DeadLine check)
## Vulnerability Detail
the protocol missing the DEADLINE check at all in logic. 

this is actually how uniswap implemented the **Deadline**, this protocol also need deadline check like this logic 

https://github.com/Uniswap/v2-periphery/blob/0335e8f7e1bd1e8d8329fd300aea2ef2f36dd19f/contracts/UniswapV2Router02.sol#L61
```solidity

// **** ADD LIQUIDITY ****
function _addLiquidity(
	address tokenA,
	address tokenB,
	uint amountADesired,
	uint amountBDesired,
	uint amountAMin,
	uint amountBMin
) internal virtual returns (uint amountA, uint amountB) {
	// create the pair if it doesn't exist yet
	if (IUniswapV2Factory(factory).getPair(tokenA, tokenB) == address(0)) {
		IUniswapV2Factory(factory).createPair(tokenA, tokenB);
	}
	(uint reserveA, uint reserveB) = UniswapV2Library.getReserves(factory, tokenA, tokenB);
	if (reserveA == 0 && reserveB == 0) {
		(amountA, amountB) = (amountADesired, amountBDesired);
	} else {
		uint amountBOptimal = UniswapV2Library.quote(amountADesired, reserveA, reserveB);
		if (amountBOptimal <= amountBDesired) {
			require(amountBOptimal >= amountBMin, 'UniswapV2Router: INSUFFICIENT_B_AMOUNT');
			(amountA, amountB) = (amountADesired, amountBOptimal);
		} else {
			uint amountAOptimal = UniswapV2Library.quote(amountBDesired, reserveB, reserveA);
			assert(amountAOptimal <= amountADesired);
			require(amountAOptimal >= amountAMin, 'UniswapV2Router: INSUFFICIENT_A_AMOUNT');
			(amountA, amountB) = (amountAOptimal, amountBDesired);
		}
	}
}

function addLiquidity(
	address tokenA,
	address tokenB,
	uint amountADesired,
	uint amountBDesired,
	uint amountAMin,
	uint amountBMin,
	address to,
	uint deadline
) external virtual override ensure(deadline) returns (uint amountA, uint amountB, uint liquidity) {
	(amountA, amountB) = _addLiquidity(tokenA, tokenB, amountADesired, amountBDesired, amountAMin, amountBMin);
	address pair = UniswapV2Library.pairFor(factory, tokenA, tokenB);
	TransferHelper.safeTransferFrom(tokenA, msg.sender, pair, amountA);
	TransferHelper.safeTransferFrom(tokenB, msg.sender, pair, amountB);
	liquidity = IUniswapV2Pair(pair).mint(to);
}
```
the point is the deadline check
```solidity
modifier ensure(uint deadline) {
	require(deadline >= block.timestamp, 'UniswapV2Router: EXPIRED');
	_;
}
```

The deadline check ensure that the transaction can be executed on time and the expired transaction revert.
## Impact

The transaction can be pending in mempool for a long and the trading activity is very time senstive. Without deadline check, the trade transaction can be executed in a long time after the user submit the transaction, at that time, the trade can be done in a sub-optimal price, which harms user's position.

The deadline check ensure that the transaction can be executed on time and the expired transaction revert.
## Code Snippet
```solidity
 function _deposit(
        uint256 amount0Desired,
        uint256 amount1Desired,
        uint256 _totalSupply,
        Slot0Data[] memory slots
    ) private {
        uint128 liquidity;
        uint256 fee0;
        uint256 fee1;
        uint256 posNum = multiPosition.length;
        PositionInfo memory position;
        for (uint256 i = 0; i < posNum; ) {
            position = multiPosition[i];

            liquidity = _calcLiquidityAmountToDeposit(
                slots[i].currentSqrtRatioX96,
                position,
                amount0Desired,
                amount1Desired
            );
            if (liquidity > 0) {
                (, , , uint128 tokensOwed0Before, uint128 tokensOwed1Before) = IUniswapV3Pool(
                    position.poolAddress
                ).positions(position.positionKey);

                IUniswapV3Pool(position.poolAddress).mint(
                    address(this), //recipient
                    position.lowerTick,
                    position.upperTick,
                    liquidity,
                    abi.encode(position.poolFeeAmt)
                );

                (, , , uint128 tokensOwed0After, uint128 tokensOwed1After) = IUniswapV3Pool(
                    position.poolAddress
                ).positions(position.positionKey);

                fee0 += tokensOwed0After - tokensOwed0Before;
                fee1 += tokensOwed1After - tokensOwed1Before;

                IUniswapV3Pool(position.poolAddress).collect(
                    address(this),
                    position.lowerTick,
                    position.upperTick,
                    type(uint128).max,
                    type(uint128).max
                );
            }
            unchecked {
                ++i;
            }
        }

```
https://github.com/sherlock-audit/2023-06-real-wagmi/blob/main/concentrator/contracts/Multipool.sol#L360
https://github.com/sherlock-audit/2023-06-real-wagmi/blob/main/concentrator/contracts/Multipool.sol#L433
https://github.com/sherlock-audit/2023-06-real-wagmi/blob/main/concentrator/contracts/Multipool.sol#L557
https://github.com/sherlock-audit/2023-06-real-wagmi/blob/main/concentrator/contracts/Dispatcher.sol#L180

## Tool used

Manual Review

## Recommendation
- consider adding deadline check like in the functions like withdraw and deposit and all operations 
the point is the deadline check
```solidity
modifier ensure(uint deadline) {
	require(deadline >= block.timestamp, 'UniswapV2Router: EXPIRED');
	_;
}
```