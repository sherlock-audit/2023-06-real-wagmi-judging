0xAsen

medium

# Factory.sol#deploy doesn't work correctly on zkSync Era

## Summary
The deploy function doesn't work correctly on zkSync Era as the compiler must be aware of the bytecode of the deployed contract in advance. 
## Vulnerability Detail
There are some differences between Ethereum and zkSync Era. For the create and create2 functions to work as expected, the compiler needs to be aware of the bytecode of the deployed contract in advance. [Link to the docs here](https://era.zksync.io/docs/reference/architecture/differences-with-ethereum.html#evm-instructions).

Here is how the deploy function is currently implemented:
```solidity
function deploy(bytes32 salt, bytes memory bytecode) private returns (address contractAddress) {
        assembly {
            contractAddress := create2(0, add(bytecode, 32), mload(bytecode), salt)
        }
        require(contractAddress != address(0), "Failed on deploy");
    }
``` 
which is exactly like the wrong implementation mentioned in the docs:
```solidity
function myFactory(bytes memory bytecode) public {
   assembly {
      addr := create(0, add(bytecode, 0x20), mload(bytecode))
   }
}
``` 
## Impact
This could lead to compile-time errors and possible failure of deploying the contracts.
## Code Snippet
https://github.com/sherlock-audit/2023-06-real-wagmi/blob/main/concentrator/contracts/Factory.sol#L58
## Tool used

Manual Review

## Recommendation
Generate the bytecode for the contract in advance. This is one possible implementation:
```solidity
bytes memory bytecode = type(MyContract).creationCode;
assembly {
    addr := create2(0, add(bytecode, 32), mload(bytecode), salt)
}
``` 