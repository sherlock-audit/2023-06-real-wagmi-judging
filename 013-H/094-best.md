ast3ros

medium

# No slippage protection when withdrawing and providing liquidity in rebalanceAll

## Summary

When `rebalanceAll` is called, the liquidity is first withdrawn from the pools and then deposited to new positions. However, there is no slippage protection for these operations.

## Vulnerability Detail

In the `rebalanceAll` function, it first withdraws all liquidity from the pools and deposits all liquidity to new positions.

        _withdraw(_totalSupply, _totalSupply);

https://github.com/sherlock-audit/2023-06-real-wagmi/blob/main/concentrator/contracts/Multipool.sol#L853-L853

        _deposit(reserve0, reserve1, _totalSupply, slots);

https://github.com/sherlock-audit/2023-06-real-wagmi/blob/main/concentrator/contracts/Multipool.sol#L885-L885

However, there are no parameters for `amount0Min` and `amount1Min`, which are used to prevent slippage. These parameters should be checked to create slippage protections.

https://docs.uniswap.org/contracts/v3/guides/providing-liquidity/decrease-liquidity
https://docs.uniswap.org/contracts/v3/guides/providing-liquidity/increase-liquidity

Actually, they are implemented in the `deposit` and `withdraw` functions, but just not in the rebalanceAll function.

https://github.com/sherlock-audit/2023-06-real-wagmi/blob/main/concentrator/contracts/Multipool.sol#L437-L438
https://github.com/sherlock-audit/2023-06-real-wagmi/blob/main/concentrator/contracts/Multipool.sol#L559-L560


## Impact

The withdraw and provide liquidity operations in rebalanceAll are exposed to high slippage and could result in a loss for LPs of multipool.

## Code Snippet

https://github.com/sherlock-audit/2023-06-real-wagmi/blob/main/concentrator/contracts/Multipool.sol#L853-L853
https://github.com/sherlock-audit/2023-06-real-wagmi/blob/main/concentrator/contracts/Multipool.sol#L885-L885

## Tool used

Manual Review

## Recommendation

Implement slippage protection in rebalanceAll as suggested to avoid loss to the protocol.