# Issue H-1: Incorrect order when calling `getAmountOut` calculates incorrectly the amount swapped 

Source: https://github.com/sherlock-audit/2023-06-real-wagmi-judging/issues/47 

## Found by 
stopthecap
## Summary
Incorrect order when calling `getAmountOut` calculates incorrectly the amount swapped

## Vulnerability Detail
When `rebalancingAll()` a certain `amountIn` is sent to be swapped in the aggregator that real wagmi chooses.

```@solidity
 _approveToken(params.zeroForOne ? token0 : token1, params.swapTarget, params.amountIn);
            (bool success, ) = params.swapTarget.call(params.swapData);
```

after the swap, the do check both balances of both tokens to see how much of each token as been sent and got back:

```@solidity
uint reserve0 = IERC20(token0).balanceOf(address(this));
        uint reserve1 = IERC20(token1).balanceOf(address(this));
```

They do make the exact calculation to determine the exact amount swapped: 

```@solidity
 uint256 amountOut = params.zeroForOne
            ? reserve1 - reserve1Before
            : reserve0 - reserve0Before;
```

and for the `amountOut` they check the `getAmountOut()` function that does return the expected amount out that you would get at  that exact time for the `amountIn` sent:   

```@solidity
 uint256 swappedOut = getAmountOut(params.zeroForOne, amountIn);
        if (amountOut < swappedOut) {
            ErrLib.requirement(
                (swappedOut * maxTwapDeviation) / MAX_WEIGHT_UINT256 >= swappedOut - amountOut,
                ErrLib.ErrorCode.PRICE_SLIPPAGE_CHECK
            );
```

The problem is that `getAmountOut` has already been updated after swapping on the wagmi's desired pool, having a divergence in price with the actual `amount` of the swap they did, moving the `reserves` of each token and its `amountsOut`

Therefore the calculation of the `if (amountOut < swappedOut) {` will be wrong, and depending where the reserves and the calculation will move, either the function will fail, or you will accept more slippage, potentially losing tokens, than the intended.

## Impact
Depending where the reserves and the calculation will move, either the function will fail, or you will accept more slippage, potentially losing tokens, than the intended.

## Code Snippet
https://github.com/sherlock-audit/2023-06-real-wagmi/blob/main/concentrator/contracts/Multipool.sol#L845-L881

https://github.com/sherlock-audit/2023-06-real-wagmi/blob/main/concentrator/contracts/Multipool.sol#L875
## Tool used

Manual Review

## Recommendation
Move the `getAmountOut` call to before the swap happened, not after



## Discussion

**ctf-sec**

@fann95 senior watson's finding, would love sponsor to comment.

cc @0xffff11 

**0xffff11**

So basically, first, this is not a duplicate of #50 . This issue presents the miss-calculation of slippage. They are sending an amountIn of let's say 100 USDC, after the swap they are calculating how much slippage should they accept is the would send 100 USDC and then checking it. You see the problem? As they are checking how much they would get in return after the swap (the values/amounts/ratios) have already changed. Therefore, the slippage will be calculated wrongly allowing the trader to loss funds due to miss-calculation. The amountOut should be calculated before swapping, not after, because the amounts will have changed.

In regards to issue #50 . It is different to this one. As they said and pointed on the issues, they are going to perform the swap in aggregators like 1inch. But, after, the slippage is calculated in Uniswap. Therefore the amounts/slippage in 1inch is definitely much different than the one in uniswap, which also miss-calculates the slippage. 

As you can see, on issue does not fix the other, that is why there are not dups. The DEXs to which you swap and calculate slippage from should be the same and you should calculate the slippage first, not after.




# Issue H-2: Wrong calculation of `tickCumulatives` due to hardcoded pool fees 

Source: https://github.com/sherlock-audit/2023-06-real-wagmi-judging/issues/48 

## Found by 
Bauchibred, OxZ00mer, ast3ros, bitsurfer, crimson-rat-reach, duc, josephdara, mahdiRostami, n1punp, n33k, shogoki, stopthecap
## Summary
Wrong calculation of `tickCumulatives` due to hardcoded pool fees

## Vulnerability Detail
Real Wagmi is using a hardcoded `500` fee to calculate the `amountOut` to check for slippage and revert if it was to high, or got less funds back than expected. 

```@solidity
 IUniswapV3Pool(underlyingTrustedPools[500].poolAddress)
```

There are several problems with the hardcoding of the `500` as the fee.

- Not all tokens have `500` fee pools
- The swapping takes place in pools that don't have a `500` fee
- The `500` pool fee is not the optimal to fetch the `tickCumulatives` due to low volume

Specially as they are deploying in so many secondary chains like Kava, this will be a big problem pretty much in every transaction over there.

If any of those scenarios is given, `tickCumulatives`  will be incorrectly calculated and it will set an incorrect slippage return.

## Impact
Incorrect slippage calculation will increase the risk of `rebalanceAll()` rebalance getting rekt.

## Code Snippet
https://github.com/sherlock-audit/2023-06-real-wagmi/blob/main/concentrator/contracts/Multipool.sol#L816-L838
https://github.com/sherlock-audit/2023-06-real-wagmi/blob/main/concentrator/contracts/Multipool.sol#L823
## Tool used

Manual Review

## Recommendation
Consider allowing the fees as an input and consider not even picking low TVL pools with no transations



## Discussion

**ctf-sec**

There are pools that are support not only 500 fee tiers

because the impact result in Incorrect slippage calculation

the severity is still high

# Issue H-3: Non deposited amount is not returned to the user 

Source: https://github.com/sherlock-audit/2023-06-real-wagmi-judging/issues/84 

## Found by 
duc, rogue-lion-0619, stopthecap, toshii
## Summary
Non deposited amount is not returned to the user

## Vulnerability Detail
When providing liquidity to uniswap/fork of uni, users are sending a preliminary `amount1Desired` and `amount0Desired` of both tokens to the multipool contract.
 
https://github.com/sherlock-audit/2023-06-real-wagmi/blob/main/concentrator/contracts/Multipool.sol#L478-L481

When calling `_deposit` an optimal amount of `liquidity` is calculated according to the following formula:

https://github.com/sherlock-audit/2023-06-real-wagmi/blob/main/concentrator/contracts/Multipool.sol#L374-L379

The liquidity calculated by the multipool contract is passed as the mint param:

https://github.com/sherlock-audit/2023-06-real-wagmi/blob/main/concentrator/contracts/Multipool.sol#L385-L391

and then it gets calculated the exact amounts to send on the mint callback by uniswap, by checking the ticks:

```@solidity
 if (params.liquidityDelta != 0) {
            if (_slot0.tick < params.tickLower) {
                // current tick is below the passed range; liquidity can only become in range by crossing from left to
                // right, when we'll need _more_ token0 (it's becoming more valuable) so user must provide it
                amount0 = SqrtPriceMath.getAmount0Delta(
                    TickMath.getSqrtRatioAtTick(params.tickLower),
                    TickMath.getSqrtRatioAtTick(params.tickUpper),
                    params.liquidityDelta
                );
            } else if (_slot0.tick < params.tickUpper) {
                // current tick is inside the passed range
                uint128 liquidityBefore = liquidity; // SLOAD for gas optimization

                // write an oracle entry
                (slot0.observationIndex, slot0.observationCardinality) = observations.write(
                    _slot0.observationIndex,
                    _blockTimestamp(),
                    _slot0.tick,
                    liquidityBefore,
                    _slot0.observationCardinality,
                    _slot0.observationCardinalityNext
                );

                amount0 = SqrtPriceMath.getAmount0Delta(
                    _slot0.sqrtPriceX96,
                    TickMath.getSqrtRatioAtTick(params.tickUpper),
                    params.liquidityDelta
                );
                amount1 = SqrtPriceMath.getAmount1Delta(
                    TickMath.getSqrtRatioAtTick(params.tickLower),
                    _slot0.sqrtPriceX96,
                    params.liquidityDelta
                );

                liquidity = LiquidityMath.addDelta(liquidityBefore, params.liquidityDelta);
            } else {
                // current tick is above the passed range; liquidity can only become in range by crossing from right to
                // left, when we'll need _more_ token1 (it's becoming more valuable) so user must provide it
                amount1 = SqrtPriceMath.getAmount1Delta(
                    TickMath.getSqrtRatioAtTick(params.tickLower),
                    TickMath.getSqrtRatioAtTick(params.tickUpper),
                    params.liquidityDelta
                );
```

Therefore, the `amount1Desired` and `amount0Desired`  sent to multipool, are not the same amounts that uniswap will request to the multipool contract through the callback  `amount1Desired` and `amount0Desired`   and the actual amounts sent, are not reimbursed to the user, causing him to loss a portion of the funds he sent.

## Impact
Loss of funds for users depositing due to no reimbursement of liquidity not requested by uniswaps callback

## Code Snippet
https://github.com/sherlock-audit/2023-06-real-wagmi/blob/main/concentrator/contracts/Multipool.sol#L360-L416
https://github.com/sherlock-audit/2023-06-real-wagmi/blob/main/concentrator/contracts/Multipool.sol#L361-L362
https://github.com/sherlock-audit/2023-06-real-wagmi/blob/main/concentrator/contracts/Multipool.sol#L389
## Tool used

Manual Review

## Recommendation
Calculate the amount before and after sending the amounts to uniswap and compare them to what the user sent. The remaining, must be reimbursed, and here is the place you can substract any fee if needed too.



## Discussion

**ctf-sec**

The report and the duplicate demonstrate the amount1Desired and amount0Desired does not match the amount1 and amount0 used because the ticker price range, think this one is still high severity

**0xffff11**

Agree with Lead Judge

# Issue H-4: Reserves calculation of Multipool contract is incorrect 

Source: https://github.com/sherlock-audit/2023-06-real-wagmi-judging/issues/88 

## Found by 
0xhacksmithh, 0xpinky, Juntao, crimson-rat-reach, duc, mrvincere, tank, toshii
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



## Discussion

**0xffff11**

I think the issue is valid. Disagree with sponsor. 

**ctf-sec**

Agree with the lead senior watson

# Issue H-5: No slippage protection when withdrawing and providing liquidity in rebalanceAll 

Source: https://github.com/sherlock-audit/2023-06-real-wagmi-judging/issues/94 

## Found by 
ast3ros, moneyversed, tank
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

# Issue H-6: Usage of `slot0` is extremely easy to manipulate 

Source: https://github.com/sherlock-audit/2023-06-real-wagmi-judging/issues/97 

## Found by 
BugBusters, Jaraxxus, ash, bitsurfer, kutugu, ni8mare, rogue-lion-0619, sashik\_eth, shealtielanz, stopthecap, toshii, tsvetanovv
## Summary
Usage of `slot0` is extremely easy to manipulate 

## Vulnerability Detail
Real Wagmi is using  `slot0` to calculate several variables in their codebase:

https://github.com/sherlock-audit/2023-06-real-wagmi/blob/main/concentrator/contracts/Multipool.sol#L589-L596

  [slot0](https://docs.uniswap.org/contracts/v3/reference/core/interfaces/pool/IUniswapV3PoolState#slot0) is the most recent data point and is therefore extremely easy to manipulate.

Multipool directly uses the token values returned by `getAmountsForLiquidity` 

```@solidity
 (uint256 amount0, uint256 amount1) = LiquidityAmounts.getAmountsForLiquidity(
                slots[i].currentSqrtRatioX96,
                TickMath.getSqrtRatioAtTick(position.lowerTick),
                TickMath.getSqrtRatioAtTick(position.upperTick),
                liquidity
            );
```

to calculate the reserves. 

```@solidity
 reserve0 += amount0;
 reserve1 += amount1;
```
Which they are used to calculate the `lpAmount` to mint from the pool. This allows a malicious user to manipulate the amount of the minted by a user.
https://github.com/sherlock-audit/2023-06-real-wagmi/blob/main/concentrator/contracts/Multipool.sol#L483

https://github.com/sherlock-audit/2023-06-real-wagmi/blob/main/concentrator/contracts/Multipool.sol#L458




## Impact
Pool lp value can be manipulated and cause other users to receive less lp tokens.

## Code Snippet
https://github.com/sherlock-audit/2023-06-real-wagmi/blob/main/concentrator/contracts/Multipool.sol#L589-L596
https://github.com/sherlock-audit/2023-06-real-wagmi/blob/main/concentrator/contracts/Multipool.sol#L754-L755
https://github.com/sherlock-audit/2023-06-real-wagmi/blob/main/concentrator/contracts/Multipool.sol#L749
https://github.com/sherlock-audit/2023-06-real-wagmi/blob/main/concentrator/contracts/Multipool.sol#L289
## Tool used

Manual Review

## Recommendation
To make any calculation use a TWAP instead of slot0.

# Issue H-7: Fees are lost if fee growth surpasses user's share value 

Source: https://github.com/sherlock-audit/2023-06-real-wagmi-judging/issues/107 

## Found by 
0xDjango, 0xdice91, 0xpinky, crimson-rat-reach, seerether, shealtielanz, stopthecap, tsvetanovv
## Summary
In `Dispatcher.sol`, when a user withdraws LP, the fees that are owed to them is subtracted from their current LP balance. In the case where the position’s earned fees outweigh the position’s current shares, claiming fees will cause a revert due to underflow.

If trading volume within the UniV3 position ticks are substantial, it can be expected that fees can outweigh initial value within a reasonable amount of time (1 to 2 years).

## Vulnerability Detail
Quite simply, since the fees are subtracted from the user's LP balance, if the fees amount to more than the initial value of the deposit, fee withdrawal will revert due to underflow.

In order to withdraw the original LP value, the user must withdraw while declining receiving the fees.

## Impact
- Loss of earned fees

## Code Snippet
https://github.com/sherlock-audit/2023-06-real-wagmi/blob/82a234a5c2c1fc1921c63265a9349b71d84675c4/concentrator/contracts/Dispatcher.sol#L236
```solidity
    function withdraw(uint256 pid, uint256 amount, uint256 deviationBP) external checkPid(pid) {
        ...

        } else if (amount < user.shares) {
            uint256 lpAmount;
            {
                (uint256 fee0, uint256 fee1) = _calcFees(feesGrow, user);
                lpAmount = _estimateWithdrawalLp(reserve0, reserve1, _totalSupply, fee0, fee1);
            }
            user.shares -= lpAmount;
```

## Tool used
Manual Review

## Recommendation
Do not subtract fees from LP balance.



## Discussion

**0xffff11**

The report clearly shows clearly shows a loss of fees. Should be a valid high imo

**ctf-sec**

Agree with the lead senior watson on this one

# Issue H-8: Divergence in calculating lp amounts will cause an imbalance depositing and withdrawing 

Source: https://github.com/sherlock-audit/2023-06-real-wagmi-judging/issues/166 

## Found by 
stopthecap
## Summary
Divergence in calculating lp amounts will cause an imbalance depositing and withdrawing 

## Vulnerability Detail

The interaction between the multipool contract and the dispacher to withdraw and deposit the lp tokens from the pool contract has a faulty logic that causes the wrong amount of lp tokens being subtracted from the users balance.

To send their lp tokens to the dispacher, users have to first deposit independently in the multipool. The calculation of the lp tokens that they receive is as follows: 

They multiply the amounts by the total supply and divide by the reserves of each token, then the lp amount of tokens minted, will be  the smaller of both

```@solidity
         uint256 l0 = (amount0Desired * _totalSupply) / reserve0; 
           uint256 l1 = (amount1Desired * _totalSupply) / reserve1; 
           lpAmount = l0 < l1 ? l0 : l1;

---------------------------------
_mint(msg.sender, lpAmount);
```

Once a user deposits on the lp tokens on the dispacher, the calculation of the lp tokens to burn, it is different to the one from the multipool. causing an error in the accounting:

```@solidity
lpAmount = _estimateWithdrawalLp(reserve0, reserve1, _totalSupply, fee0, fee1);
function _estimateWithdrawalLp(
        uint256 reserve0,
        uint256 reserve1,
        uint256 _totalSupply,
        uint256 amount0,
        uint256 amount1
    ) private pure returns (uint256 shareAmount) {
  shareAmount =
            ((amount0 * _totalSupply) / reserve0 + (amount1 * _totalSupply) / reserve1) / 2;
}
```
multiplying both supplies by the amounts, dividing by their reserves, and dividing by 2.

Therefore, you will mint the smallest amount of both calculations of lp tokens and you will burn the average amount of both calculations.

## Impact

Loss of lp tokens due to an error accounting for their amounts in between dispacher and multipool
## Code Snippet
- Dispacher: 
https://github.com/sherlock-audit/2023-06-real-wagmi/blob/main/concentrator/contracts/Dispatcher.sol#L234
https://github.com/sherlock-audit/2023-06-real-wagmi/blob/main/concentrator/contracts/Dispatcher.sol#L140-L150

- Multipool: 
https://github.com/sherlock-audit/2023-06-real-wagmi/blob/main/concentrator/contracts/Multipool.sol#L468-L471

## Tool used

Manual Review

## Recommendation
Use the exact same calculation to determine the shares to mint/burn and substract the users



## Discussion

**0xffff11**

I think the report clearly shows how the calculations differ from each other and shows the impact of it. This should be a high imo. 

# Issue H-9: Incorrect usage of slippage protection params 

Source: https://github.com/sherlock-audit/2023-06-real-wagmi-judging/issues/180 

## Found by 
0xpinky, crimson-rat-reach, ginlee, minhtrng, oxcm, rogue-lion-0619, talfao
## Summary

The parameters passed as slippage protection are used incorrectly, causing users to overpay.

## Vulnerability Detail

The function `deposit` receives the parameters `amount0Min` and `amount1Min` which are meant to be for slippage protection:

```js
@param amount0Min The minimum amount of token0 required to be deposited.
@param amount1Min The minimum amount of token1 required to be deposited.
```

These parameters are used within `_optimizeAmounts` to recalculate the values for `amount0Desired/amount1Desired`:

```js
//in deposit
(amount0Desired, amount1Desired) = _optimizeAmounts(
    amount0Desired,
    amount1Desired,
    amount0Min,
    amount1Min,
    reserve0,
    reserve1
);

// in _optimizeAmounts
if (reserve0 == 0 && reserve1 == 0) {
    (amount0, amount1) = (amount0Desired, amount1Desired);
} else {
    uint256 amount1Optimal = _quote(amount0Desired, reserve0, reserve1);
    if (amount1Optimal <= amount1Desired) {
        ErrLib.requirement(
            amount1Optimal >= amount1Min,
            ErrLib.ErrorCode.INSUFFICIENT_1_AMOUNT
        );
        (amount0, amount1) = (amount0Desired, amount1Optimal);
    } else {
        ...
```

`_quote` uses a UniV2 sort of calculation to calculate the amountOut for an input amount:

```js
//WARDEN-NOTE: this is the quote function as found in UniswapV2Library.sol
function _quote(
    uint256 amountA,
    uint256 reserveA,
    uint256 reserveB
) private pure returns (uint256 amountB) {
    ErrLib.requirement(amountA > 0, ErrLib.ErrorCode.INSUFFICIENT_AMOUNT);
    ErrLib.requirement(reserveA > 0 && reserveB > 0, ErrLib.ErrorCode.INSUFFICIENT_LIQUIDITY);
    amountB = (amountA * reserveB) / reserveA;
}
```

However, using the results of this calculation as the "optimal amount" is false, as it does not represent the actual amount required when minting positions across the different v3 pools.

## Impact

Slippage protection does not work as intended

## Code Snippet

https://github.com/sherlock-audit/2023-06-real-wagmi/blob/main/concentrator/contracts/Multipool.sol#L459-L466

## Tool used

Manual Review

## Recommendation

The actual slippage protection as can be found in the official UniV3-periphery `LiquidityManagement.addLiquidity` should use the return values of `UniswapV3Pool.mint` and check against the slippage input params like this:

```js
(amount0, amount1) = pool.mint(
    params.recipient,
    params.tickLower,
    params.tickUpper,
    liquidity,
    abi.encode(MintCallbackData({poolKey: poolKey, payer: msg.sender}))
);

require(amount0 >= params.amount0Min && amount1 >= params.amount1Min, 'Price slippage check');
```



## Discussion

**ctf-sec**

https://docs.sherlock.xyz/audits/judging/judging#list-of-issue-categories-that-are-considered-valid

> Slippage related issues showing a definite loss of funds with a detailed explanation for the same can be considered valid high

Think the issue of the severity is still high

**0xffff11**

I agree with a high

# Issue M-1: Divergence between different DEXs when rebalancing will miss-calculate slippage 

Source: https://github.com/sherlock-audit/2023-06-real-wagmi-judging/issues/50 

## Found by 
stopthecap
## Summary
Divergence between different DEXs when rebalancing will miss-calculate slippage 

## Vulnerability Detail

When rebalancing, real wagmi does use one of their whitelisted contracts (aggregators). As said by the team, 1inch it would be an example of one. 
<img width="289" alt="image" src="https://github.com/sherlock-audit/2023-06-real-wagmi-0xffff11/assets/123578292/4dc72e86-9379-4f8f-8037-3b673466ab0e">
The problem here, is that the actual swapping for rebalancing and the calculation of the `amounOut` is made in different DEXs/aggregators.

- Swapping: 
https://github.com/sherlock-audit/2023-06-real-wagmi/blob/main/concentrator/contracts/Multipool.sol#L858-L859
- amountOut: 
https://github.com/sherlock-audit/2023-06-real-wagmi/blob/main/concentrator/contracts/Multipool.sol#L823
 Specially, as deploying in so many chains it will diverge between the DEX pool where you swap and the DEX where you calculate the `amountOut` The `amounOut` in exchange X for `token1` will be be completely different to the `amounOut` in exchange Y for `token1`, because it depends on the reserves in the actual pool.

## Impact
Error on calculating slippage through different DEXs that will cause losing funds due to missing an accurate slippage 

## Code Snippet
https://github.com/sherlock-audit/2023-06-real-wagmi/blob/main/concentrator/contracts/Multipool.sol#L823
https://github.com/sherlock-audit/2023-06-real-wagmi/blob/main/concentrator/contracts/Multipool.sol#L858-L859
## Tool used
Manual Review

## Recommendation
Do calculate the slippage from the same DEX where it was swapped



## Discussion

**ctf-sec**

@fann95 senior watson's finding, would love sponsor to comment.

cc @0xffff11 

**0xffff11**

See my comment for the non-duplication and validity in issue #47 

**ctf-sec**

@0xffff11 Is it possible to add the image? Thanks

**ctf-sec**

![image](https://github.com/sherlock-audit/2023-06-real-wagmi-judging/assets/114844362/daa1fc06-dc89-4682-b33b-40b443f88c47)


**0xffff11**

Can you see it now? https://imgur.com/3NpAuXq

**ctf-sec**

![image](https://github.com/sherlock-audit/2023-06-real-wagmi-judging/assets/114844362/8a5a98fd-387c-4ab0-8d88-14d40bbedf76)


# Issue M-2: Using only 150 blocks as `twapDuration` is very easily to manipulate in low volume pools 

Source: https://github.com/sherlock-audit/2023-06-real-wagmi-judging/issues/51 

## Found by 
Bauchibred, crimson-rat-reach, stopthecap
## Summary
Using only 150 blocks as `twapDuration` is very easy to manipulate in low volume pools 

## Vulnerability Detail

In the function `getAmountOut` there is hardcoded `150` as the twapDuration. This does mean that 
it returns the cumulative tick and liquidity as of each timestamp secondsAgo from the current block timestamp.

So it returns the TWAP `tickCumulatives` of the last 150 seconds.

Due to real wagmi deploying in a lot to secondary chains like kava and wanting to integrate with a wide variety of pools, the 150 seconds `observe` call is extreamily prone to manipulation. Specially in pools were there are no transactions in 2 minutes (pretty much more than 50% outside ethereum)

Attacker will be able to manipulate the `tickCumulatives` to affect to the amount of slippage expected during rebalances, accepting much more slippage than the contract should, losing funds.

## Impact
Loss of funds due to accepting a much higher amount of slippage because of manipulation

## Code Snippet
https://github.com/sherlock-audit/2023-06-real-wagmi/blob/main/concentrator/contracts/Multipool.sol#L821-L824
## Tool used

Manual Review

## Recommendation
Increase the TWAP duration to around a (1000)  to get an appropiate and correct exchange rate



## Discussion

**ctf-sec**

> Due to real wagmi deploying in a lot to secondary chains like kava and wanting to integrate with a wide variety of pools, the 150 seconds observe call is extreamily prone to manipulation. Specially in pools were there are no transactions in 2 minutes (pretty much more than 50% outside ethereum)

this sounds reasonable, agree that this would be a issue

**ctf-sec**

but manipulating the liquidity for 2 minutes post very significant risk on attacker's fund... will leave the severity as medium, escalation are welcome

**ctf-sec**

Will redo the de-duplicate for this one

# Issue M-3: Possible precision loss in `_checkpositionsRange` function 

Source: https://github.com/sherlock-audit/2023-06-real-wagmi-judging/issues/82 

## Found by 
0xdice91, BugBusters, ash, ginlee, josephdara, lil.eth, shealtielanz, tsvetanovv, twcctop
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



## Discussion

**0xffff11**

Seems like a valid medium to me. Reference from tickSpacing: https://docs.uniswap.org/contracts/v3/reference/core/libraries/Tick

# Issue M-4: The `_estimateWithdrawalLp` function might return a very large value, result in users losing significant incentives or being unable to withdraw from the Dispatcher contract 

Source: https://github.com/sherlock-audit/2023-06-real-wagmi-judging/issues/142 

## Found by 
Avci, BugBusters, duc, lil.eth, qpzm
## Summary
The `_estimateWithdrawalLp` function might return a very large value, result in users losing significant incentives or being unable to withdraw from the Dispatcher contract
## Vulnerability Detail
In Dispatcher contract, `_estimateWithdrawalLp` function returns the value of shares amount based on the average of ratios `amount0 / reserve0` and `amount1 / reserve1`.
```solidity=
function _estimateWithdrawalLp(
    uint256 reserve0,
    uint256 reserve1,
    uint256 _totalSupply,
    uint256 amount0,
    uint256 amount1
) private pure returns (uint256 shareAmount) {
    shareAmount =
        ((amount0 * _totalSupply) / reserve0 + (amount1 * _totalSupply) / reserve1) /
        2;
}
```
From `Dispatcher.withdraw` and `Dispatcher.deposit` function, amount0 and amount1 will be the accumulated fees of users
```solidity=
uint256 lpAmount;
{
    (uint256 fee0, uint256 fee1) = _calcFees(feesGrow, user);
    lpAmount = _estimateWithdrawalLp(reserve0, reserve1, _totalSupply, fee0, fee1);
}
user.shares -= lpAmount;
_withdrawFee(pool, lpAmount, reserve0, reserve1, _totalSupply, deviationBP);
```
However, it is important to note that the values of reserve0 and reserve1 can fluctuate significantly. This is because the positions of the Multipool in UniSwapV3 pools (concentrated) are unstable on-chain, and they can change substantially as the state of the pools changes. As a result, the `_estimateWithdrawalLp` function might return a large value even for a small fee amount. This could potentially lead to reverting due to underflow in the deposit function (in cases where `lpAmount > user.shares`), or it could result in withdrawing a larger amount of Multipool LP than initially expected.

Scenario:
1. Total supply of Multipool is 1e18, and Alice has 1e16  (1%) LP amounts which deposited into Dispatcher contract.
2. Alice accrued fees = 200 USDC and 100 USDT
3. The reserves of Multipool are 100,000 USDC and 100,000 USDT, `_estimateWithdrawalLp` of Alice fees will be `(0.2% + 0.1%) / 2 * totalSupply` = `0.15% * totalSupply` = 1.5e15 LP amounts
4. However, in some cases, UniSwapV3 pools may experience fluctuations, reserves of Multipool are 10,000 USDC and 190,000 USDT, `_estimateWithdrawalLp` of Alice fees will be `(2% + 0.052%) / 2 * totalSupply` = `1.026% * totalSupply` = 1.026e16 LP amounts
This result is greater than LP amounts of Alice (1e16), leading to reverting by underflow in deposit/withdraw function of Dispatcher contract.
## Impact
Users may face 2 potential issues when interacting with the Dispatcher contract. 
1. They might be unable to deposit/withdraw
2. Secondly, users could potentially lose significant incentives when depositing or withdrawing due to unexpected withdrawals of LP amounts for their fees.
## Code Snippet
https://github.com/sherlock-audit/2023-06-real-wagmi/blob/main/concentrator/contracts/Dispatcher.sol#L140-L150
## Tool used
Manual review

## Recommendation
Shouldn't use the average ratio for calculation in`_estimateWithdrawalLp` function



## Discussion

**ctf-sec**

Think can change the severity to medium

# Issue M-5: The deposit 

Source: https://github.com/sherlock-audit/2023-06-real-wagmi-judging/issues/163 

## Found by 
Avci, Phantasmagoria, kutugu, sashik\_eth, shealtielanz
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



## Discussion

**ctf-sec**

Seems like the sponsor mark https://github.com/sherlock-audit/2023-06-real-wagmi-judging/issues/102 as medium and dispute #163

#116 is a duplicate of #102 as well,

I understand the sponsor is mainly concerning with rebalance action.

Recommend still leave this issue as a medium

**0xffff11**

Agree to keep a med here

