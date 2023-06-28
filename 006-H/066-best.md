talfao

medium

# Loss of funds of the user due to incorrect lpToken calculation

## Summary
When the user deposits assets to the Multipool and withdraw them back immediately, they will suffer from such an unexpected loss of funds. This is probably done due to 2 problems. The first is about the calculation of a number of LpTokens.
## Vulnerability Detail
The user decides to deposit assets to the Multipool so that he will call the deposit function. But before that, it is good to call estimateDepositAmounts to get the correct number of assets to be put into the pool. After that, the user call the deposit function to deposit assets and withdraw to get his assets back.

The user should get the same amount of tokens as the liquidity providing should be without fee. However, they lose some of his funds.
The tests which well inserted into the original file of tests.
```Javascript
 it("should make a deposit successfully", async () => {
        let usdtAmountToDeposit = ethers.utils.parseUnits("1000", 6);
        let wethAmountToDeposit = await factory.getQuoteAtTick(
            500,
            usdtAmountToDeposit,
            USDT.address,
            WETH.address
        );

        //                        token0 ==weth        token1 ==usdt
        await multipool.connect(manager).deposit(wethAmountToDeposit, usdtAmountToDeposit, 0, 0);

        [usdtAmountToDeposit, wethAmountToDeposit] = await factory.estimateDepositAmounts(
            USDT.address,
            WETH.address,
            usdtAmountToDeposit,
            0
        );
        let BeforeUSDTBalanceOfPool = await USDT.balanceOf(multipool.address);
        let BeforeWETHBalanceOfPool = await WETH.balanceOf(multipool.address);
        console.log("USDT before deposit", BeforeUSDTBalanceOfPool);
        console.log("Weth before deposit", BeforeWETHBalanceOfPool)
        console.log("Alice WETH before deposit", await WETH.balanceOf(alice.address));
        console.log("Alice USDT before deposit", await USDT.balanceOf(alice.address));
        console.log("What Alice deposits", "USDT:", usdtAmountToDeposit, "| WETH:", wethAmountToDeposit);
        await multipool.connect(alice).deposit(wethAmountToDeposit, usdtAmountToDeposit, wethAmountToDeposit, usdtAmountToDeposit);
        let AfterUSDTBalanceOfPool = await USDT.balanceOf(multipool.address);
        let AfterWETHBalanceOfPool = await WETH.balanceOf(multipool.address);
        console.log("USDT After aliceDeposit", AfterUSDTBalanceOfPool);
        console.log("Weth After deposit", AfterWETHBalanceOfPool)
    });

 it("MY TEST Loss of funds after withdraw", async () => {
        let lpBalAlice = await multipool.balanceOf(alice.address);
        console.log("Alice lp tokens", lpBalAlice);

        let estimated = await factory.estimateWithdrawalAmounts(USDT.address, WETH.address, lpBalAlice)
        await multipool.connect(alice).withdraw(lpBalAlice, 0, 0); // Zeroes could be change to estimated numbers and the result remains samme.
        let USDTBalanceOfPool = await USDT.balanceOf(multipool.address);
        let WETHBalanceOfPool = await WETH.balanceOf(multipool.address);
        console.log("USDT after withdraw", USDTBalanceOfPool);
        console.log("WETH after withdraw", WETHBalanceOfPool);
        console.log("Alice USDT after withdraw", await USDT.balanceOf(alice.address));
        console.log("Alice WETH after withdraw", await WETH.balanceOf(alice.address));
        console.log("What are estimated results:",);
    });
```
The original balance of the user Alice was:
```Javascript
Alice WETH before deposit  { value: "100000000000000000000" }
Alice USDT before deposit { value: "10000000000" }
```
The balance after the deposit and withdrawal:
```Javascript
Alice USDT after withdrawing { value: "9999999998" }
Alice WETH after withdrawing { value: "99999999999722195142" }
```

The one problem is how the **number of LpTokens is calculated in the deposit function**. https://github.com/sherlock-audit/2023-06-real-wagmi/blob/82a234a5c2c1fc1921c63265a9349b71d84675c4/concentrator/contracts/Multipool.sol#L470C9-L470C9

**As the lesser number of LpTokens is given, it causes some loss of funds.**
When the condition is changed, the loss is definitely smaller:

```Javascript
Alice USDT after withdrawing { value: "9999999999" }
Alice WETH after withdrawing  { value: "99999999999999990524"
``` 

### Note
*Note: The loss of funds could also occur in different calculations during the deposit. It would be good to check the whole logic to remediate this loss of funds.* 

## Impact
Due to this incorrect choice of lpTokens, the user can lose some funds. I give this issue medium as just some part of it is lost.
## Code Snippet
https://github.com/sherlock-audit/2023-06-real-wagmi/blob/82a234a5c2c1fc1921c63265a9349b71d84675c4/concentrator/contracts/Multipool.sol#L470C9-L470C9
## Tool used

Manual Review

## Recommendation
One way is to change the condition:
  ``` lpAmount = l0 > l1 ? l0 : l1; ```
The second way is to make some averages of this l0 and l1.
