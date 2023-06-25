mau

high

# Decimal precision discrepancy leads to inconsistent lpAmount calculation in liquidity pool deposit

## Summary
The identified issue relates to the calculation of the `lpAmount` (liquidity pool tokens) in a deposit function. The code calculates `lpAmount` by taking the square root of the product of `amount0Desired` and `amount1Desired`, and subtracting the `MINIMUM_LIQUIDITY` value. 

## Vulnerability Detail

However, the issue arises when dealing with stable coins that have different decimal precisions. The code does not account for this, resulting in different `lpAmount` values for the same monetary value but different stable coin pairs. For example, depositing 1.1 USD in a` DAI/USDC` pair would yield a higher `lpAmount` than depositing the same value in a `USDC/USDT` pair, despite both representing 1.1 USD. This discrepancy can lead to imbalanced liquidity allocations in the pool.

## Impact

The impact of this issue can lead to imbalanced liquidity allocations in the pool.

Consider two stable coin pairs: `DAI/USDC` and `USDC/USDT`, where `DAI` has 18 decimals, `USDC` and `USDT` has 6 decimals.

Suppose a user wants to deposit 1.1 USD into both pairs.

In the `DAI/USDC` pair, the `lpAmount` is calculated incorrectly due to the differing decimal precisions. The code may yield `lpAmount = 1099999999000` for 1.1 USD.

In the `USDC/USDT` pair, the same 1.1 USD deposit would result in a different `lpAmount`. It yields `lpAmount = 1099000`.

We have the same monetary value of 1.1 USD, but the `lpAmounts` differ significantly between the two pairs. The `lpAmount` for the `DAI/USDC` pair is much larger (1099999999000) compared to the `lpAmount` for the `USDC/USDT` pair (1099000).

This impact can create an imbalance in liquidity allocation. A user depositing the same value in different stable coin pairs would receive significantly different amounts of liquidity pool tokens. It allows an attacker or sophisticated users to exploit this imbalance, potentially manipulating the liquidity distribution and gaining an unfair advantage in the pool.

The overall impact is a violation of the intended fairness and consistency in liquidity provision, affecting the stability and efficiency of the pool.

## Code Snippet

https://github.com/sherlock-audit/2023-06-real-wagmi/blob/82a234a5c2c1fc1921c63265a9349b71d84675c4/concentrator/contracts/Multipool.sol#L453
## Tool used

Manual Review

## Recommendation

Modify the code to calculate `lpAmount` accurately by considering the decimal precisions of the stable coins involved. Ensure that the square root calculation accounts for the correct number of decimals for each token. This will result in consistent and fair `lpAmount` calculations regardless of the stable coin pair being used.