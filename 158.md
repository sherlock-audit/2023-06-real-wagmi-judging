0xJuda

medium

# User loses funds when withdrawing right after depositing

## Summary
Users who withdraw right after depositing their funds to Wagmi lose part of their assets.

## Vulnerability Detail
User can deposit funds to gain fees from liquidity providing. He may change his mind and decides to withdraw funds right after depositing them. This will cost him some funds that will be left in Uniswap pools and in Multipool as well.

I created a new test **should make a deposit and withdraw right after it successfully** for this. You can find it in detail below. I inserted it right before the **should make a deposit successfully**.

<details>
  <summary markdown="span">New 'should make a deposit and withdraw right after it successfully' test</summary>

```typescript
it("should make a deposit and withdraw right after it successfully", async () => {
    // Initial multipool deposit
    let usdtAmountToDeposit = ethers.utils.parseUnits("1000", 6);
    let wethAmountToDeposit = await factory.getQuoteAtTick(
        500,
        usdtAmountToDeposit,
        USDT.address,
        WETH.address
    );
    //                        token0 ==weth        token1 ==usdt
    await multipool.connect(manager).deposit(wethAmountToDeposit, usdtAmountToDeposit, 0, 0);

    // Helper function
    const getBalance = async (contract: any, account: any): Promise<BigNumber> => contract.balanceOf(account.address);

    // Get initial balances
    const aliceUSDTBefore = await getBalance(USDT, alice);
    const aliceWETHBefore = await getBalance(WETH, alice);

    const pool500USDTBefore = await getBalance(USDT, pool500);
    const pool500WETHBefore = await getBalance(WETH, pool500);

    const pool10000USDTBefore = await getBalance(USDT, pool10000);
    const pool10000WETHBefore = await getBalance(WETH, pool10000);

    const pool3000USDTBefore = await getBalance(USDT, pool3000);
    const pool3000WETHBefore = await getBalance(WETH, pool3000);

    const multipoolUSDTBefore = await getBalance(USDT, multipool);
    const multipoolWETHBefore = await getBalance(WETH, multipool);

    // Deposit
    [usdtAmountToDeposit, wethAmountToDeposit] = await factory.estimateDepositAmounts(
        USDT.address,
        WETH.address,
        usdtAmountToDeposit,
        0
    );
    // 0.1% slippage
    const usdtAmountToDepositMin = usdtAmountToDeposit.mul(9990).div(10000);
    const wethAmountToDepositMin = wethAmountToDeposit.mul(9990).div(10000);

    await multipool.connect(alice).deposit(wethAmountToDeposit, usdtAmountToDeposit, wethAmountToDepositMin, usdtAmountToDepositMin);

    // Withdraw
    const lpAmount = await multipool.balanceOf(alice.address);

    let amount0Min: BigNumber;
    let amount1Min: BigNumber;

    [amount0Min, amount1Min] = await factory.estimateWithdrawalAmounts(
        USDT.address,
        WETH.address,
        lpAmount
    );
    // 0.1% slippage
    amount0Min = amount0Min.mul(9990).div(10000);
    amount1Min = amount1Min.mul(9990).div(10000);

    await multipool.connect(alice).withdraw(lpAmount, amount0Min, amount1Min);

    // Calculate final balances and differences
    const aliceUSDTAfter = await USDT.balanceOf(alice.address);
    const aliceWETHAfter = await WETH.balanceOf(alice.address);

    const aliceDifferenceUSDT = aliceUSDTAfter.sub(aliceUSDTBefore);
    const aliceDifferenceWETH = aliceWETHAfter.sub(aliceWETHBefore);

    const pool500USDTAfter = await getBalance(USDT, pool500);
    const pool500WETHAfter = await getBalance(WETH, pool500);

    const pool500DifferenceUSDT = pool500USDTAfter.sub(pool500USDTBefore);
    const pool500DifferenceWETH = pool500WETHAfter.sub(pool500WETHBefore);

    const pool3000USDTAfter = await getBalance(USDT, pool3000);
    const pool3000WETHAfter = await getBalance(WETH, pool3000);

    const pool3000DifferenceUSDT = pool3000USDTAfter.sub(pool3000USDTBefore);
    const pool3000DifferenceWETH = pool3000WETHAfter.sub(pool3000WETHBefore);

    const pool10000USDTAfter = await getBalance(USDT, pool10000);
    const pool10000WETHAfter = await getBalance(WETH, pool10000);

    const pool10000DifferenceUSDT = pool10000USDTAfter.sub(pool10000USDTBefore);
    const pool10000DifferenceWETH = pool10000WETHAfter.sub(pool10000WETHBefore);

    const multipoolUSDTAfter = await getBalance(USDT, multipool);
    const multipoolWETHAfter = await getBalance(WETH, multipool);

    const multipoolDifferenceUSDT = multipoolUSDTAfter.sub(multipoolUSDTBefore);
    const multipoolDifferenceWETH = multipoolWETHAfter.sub(multipoolWETHBefore);

    // Log gathered data
    console.log('-------------------------------------------------------');
    console.log('Alice');
    console.log('|  USDT');
    console.log('|      Before:', aliceUSDTBefore.toString());
    console.log('|      After:  ', aliceUSDTAfter.toString());
    console.log('|      Difference:', aliceDifferenceUSDT.toString());
    console.log('|  WETH');
    console.log('|      Before:', aliceWETHBefore.toString());
    console.log('|      After:  ', aliceWETHAfter.toString());
    console.log('|      Difference:', aliceDifferenceWETH.toString());
    console.log('-------------------------------------------------------');
    console.log('Multipool');
    console.log('|  USDT');
    console.log('|      Before:', multipoolUSDTBefore.toString());
    console.log('|      After: ', multipoolUSDTAfter.toString());
    console.log('|      Difference:', multipoolDifferenceUSDT.toString());
    console.log('|  WETH');
    console.log('|      Before:', multipoolWETHBefore.toString());
    console.log('|      After: ', multipoolWETHAfter.toString());
    console.log('|      Difference:', multipoolDifferenceWETH.toString());
    console.log('-------------------------------------------------------');
    console.log('Uniswap Pool 500');
    console.log('|  USDT');
    console.log('|      Before:', pool500USDTBefore.toString());
    console.log('|      After: ', pool500USDTAfter.toString());
    console.log('|      Difference:', pool500DifferenceUSDT.toString());
    console.log('|  WETH');
    console.log('|      Before:', pool500WETHBefore.toString());
    console.log('|      After: ', pool500WETHAfter.toString());
    console.log('|      Difference:', pool500DifferenceWETH.toString());
    console.log('-------------------------------------------------------');
    console.log('Uniswap Pool 3000');
    console.log('|  USDT');
    console.log('|      Before:', pool3000USDTBefore.toString());
    console.log('|      After: ', pool3000USDTAfter.toString());
    console.log('|      Difference:', pool3000DifferenceUSDT.toString());
    console.log('|  WETH');
    console.log('|      Before:', pool3000WETHBefore.toString());
    console.log('|      After: ', pool3000WETHAfter.toString());
    console.log('|      Difference:', pool3000DifferenceWETH.toString());
    console.log('-------------------------------------------------------');
    console.log('Uniswap Pool 10000');
    console.log('|  USDT');
    console.log('|      Before:', pool10000USDTBefore.toString());
    console.log('|      After: ', pool10000USDTAfter.toString());
    console.log('|      Difference:', pool10000DifferenceUSDT.toString());
    console.log('|  WETH');
    console.log('|      Before:', pool10000WETHBefore.toString());
    console.log('|      After: ', pool10000WETHAfter.toString());
    console.log('|      Difference:', pool10000DifferenceWETH.toString());
    console.log('-------------------------------------------------------');

    expect(aliceUSDTAfter).to.be.greaterThanOrEqual(aliceUSDTBefore);
    expect(aliceWETHAfter).to.be.greaterThanOrEqual(aliceWETHBefore);
});
```
</details>

Outcome of this test looks like this:
```text
-------------------------------------------------------
Alice
|  USDT
|      Before: 1000000000000
|      After:   999999999998
|      Difference: -2
|  WETH
|      Before: 10000000000000000000000
|      After:   9999999999999722195142
|      Difference: -277804858
-------------------------------------------------------
Multipool
|  USDT
|      Before: 496042521
|      After:  496042521
|      Difference: 0
|  WETH
|      Before: 55558873514202538
|      After:  55558873541982900
|      Difference: 27780362
-------------------------------------------------------
Uniswap Pool 500
|  USDT
|      Before: 21791296923144
|      After:  21791296923145
|      Difference: 1
|  WETH
|      Before: 14871919454727170808820
|      After:  14871919454727309711089
|      Difference: 138902269
-------------------------------------------------------
Uniswap Pool 3000
|  USDT
|      Before: 20166050769790
|      After:  20166050769791
|      Difference: 1
|  WETH
|      Before: 17423455704633477623353
|      After:  17423455704633560965061
|      Difference: 83341708
-------------------------------------------------------
Uniswap Pool 10000
|  USDT
|      Before: 1022908154012
|      After:  1022908154012
|      Difference: 0
|  WETH
|      Before: 9143921254070579260152
|      After:  9143921254070607040671
|      Difference: 27780519
-------------------------------------------------------
```

As you can see, Alice is the only one who has fewer tokens after she deposits and withdraws.

## Impact
Users lose assets if they decide to withdraw after depositing.

## Code Snippet

Tests - https://github.com/sherlock-audit/2023-06-real-wagmi/blob/main/concentrator/test/Concentrator.ts#L315C5-L334C8

Deposit function - https://github.com/sherlock-audit/2023-06-real-wagmi/blob/main/concentrator/contracts/Multipool.sol#L433

Withdraw function - https://github.com/sherlock-audit/2023-06-real-wagmi/blob/main/concentrator/contracts/Multipool.sol#L557

## Tool used

Manual Review

## Recommendation
Revisit calculations and make sure the user doesn't suffer a loss in case of withdrawing right after depositing. Create additional tests to prevent this from happening in the future.