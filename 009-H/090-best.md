OxZ00mer

medium

# Certain Multipools are very expensive to deposit into because of a very high minimum amount.

## Summary
The minimum amount for depositing in a multipool is **`1e6`**. It is not a big amount for tokens with more decimals but will be a very big amount for tokens with lower decimals and higher values like WBTC.

## Vulnerability Detail
The minimum amount of tokens for depositing in a multipool is **`1e6`**. It is not a big amount for tokens with higher decimal counts (i.e. 12+) but will be a very big amount for tokens with lower decimals and higher values like WBTC.
In the case of a WBTC-USDT pool, it will require **`1e6`** worth of BTC and an equivalent value of USDT. So in this case the value the user will need to deposit will be around 300$ worth of WBTC (by current prices) and around 300$ worth of UDST to match the WBTC amount.
So in the above-mentioned Multipool's case, the minimum deposit amount will be around 600$.

## Impact
It will make certain pools very expensive to deposit into.

## Code Snippet
https://github.com/sherlock-audit/2023-06-real-wagmi/blob/main/concentrator/contracts/Multipool.sol#L74

https://github.com/sherlock-audit/2023-06-real-wagmi/blob/main/concentrator/contracts/Multipool.sol#L440-L443

## Tool used

Manual Review

## Recommendation
Consider either making the minimum amount get set at construction time or by setting the **`MINIMUM_AMOUNT`** variable to a smaller amount like **`1e3`**.

