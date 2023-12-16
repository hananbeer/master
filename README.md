# Code MASTER

Modify ASTs Easily & Reliably

# Install

install `sol-ast-compile` tool:

```
npm install -g solc-typed-ast
```

# Usage

`ast_patcher.py` now supports argparse! here's an example showing how to chain multiple mutators:

```bash
cat ./data/build.json |
python ./src/ast_patcher.py - shadow_block |
python ./src/ast_patcher.py - function_inliner -c Zapper_Matic_Bridge_V1_1 -m ZapBridge -d 2 |
python ./src/ast_patcher.py - using_for_inliner |
python ./src/ast_patcher.py - delinearizer -c Zapper_Matic_Bridge_V1_1 |
sol-ast-compile --source --stdin --mode json
```

### Old usage:

```bash
# random chosen contract to work with
# start by flattening the solidity files into a single file
forge flatten ./data/0xe34b087bf3c99e664316a15b01e5295eb3512760/src/contracts/Polygon/Bridge/Zapper_Matic_Bridge_V1.sol > ./data/flat.sol

# generate solidity AST & build info
# optional formatting with jq
solc --combined-json ast ./data/flat.sol | jq . > ./data/build.json

# MODIFY AST HERE, e.g.:
python ./src/ast_patcher.py > ./data/magic.json

sol-ast-compile --source ./data/magic.json > ./data/rebuild.sol

# optionally format the rebuilt solidity code with (if AST is gramatically correct)
forge fmt ./data/rebuild.sol > ./data/formatted.sol
```

there's also a work in progress AST-to-source rebuilder:
```bash
python ./src/builder/main.py ./data/magic.json > ./data/rebuild.sol
```


# Notes

`solc` only preserves "doc strings" which are `/** */`

it is useful to convert `// comments` and `/* comments */` to doc strings form.

(be aware of cases such as `//` is already inside `/** */`)


# Mutators

using the AST mapper, mutators are classes that define prebuilt modification rules such

## using-for inliner

fix `using .. for ..` statements (by removing them)

example:
```py
from mutators import using_for_inliner
using_for_inliner.embed_using_for(ast)
```

input:
```solidity
using SafeERC20 for IERC20;
...
    IERC20(token).safeTransfer(target, amount);
...
```

output:
```solidity
...
    SafeERC20.safeTransfer(IERC20(token), target, amount);
...
```


## function inliner

recursively embed internal function calls into a specific function body, including modifers and constructors.

modifiers of called functions are always embedded.

set `embed_top_modifiers=True` to also embed the target function's modifiers.

set `delete_internal=True` to remove embeded function definitions after inlining them.

use `max_depth` to limit the recursion depth. (default -1 for no limit)

example:
```py
from mutators import function_inliner

# inline constructor with empty method name ("fallback" & "receive" are used by name)
function_inliner.embed_inline(ast, 'ContractName', '', embed_top_modifiers=True, max_depth=1)

# inline ZapBridge external function
function_inliner.embed_inline(ast, 'ContractName', 'MethodName', embed_top_modifiers=False, max_depth=6, delete_internal=True)
```

NOTE: the resulting code will not compile. due to lack of control flow syntax (`jump`/`goto`) it is not possible to translate early return statements. for this reason, (for the moment) the inliner does not attempt to produce valid code. example below.

input:
```solidity
function _balanceOf(address user) returns (uint256) {
    require(!_paused);
    return _balances[user];
}

function getBalance() external returns (uint256) {
    uint256 balance = _balanceOf(msg.sender);
    return balance;
}
```

output:
```solidity
function getBalance() external returns (uint256) {
    uint256 balance = {
        /// @inlined from _balanceOf
        address user = msg.sender;
        require(!_paused);
        return _balances[user];
    }
    return balance;
}
```

note the inner return statement isn't standard solidity, it actually refers to the return value of the block marked `@inlined from _balanceOf`

TODO: possibly replace with a distinct keyword, perhaps `yield` or something like that. (also need to specify the scope from which it yields since there is no distinction between blocks, yet)

also it does not yet inline the args when possible. for example here `user` can be trivially removed altogether. maybe in the future.

## delinearization

fancy name I made for flattenning inheritance. stems from [C3 linearization](https://en.wikipedia.org/wiki/C3_linearization).


example:
```py
from mutators import delinearizer
delinearizer.delinearize(ast, 'ContractName')
```

input:
```solidity
contract A {
    function a() external { .. }
}

contract B is A {
    function b() external { .. }
}

contract C is A, B {
    function c() external { .. }
}
```

output:
```solidity
contract C {
    function a() external { .. }
    function b() external { .. }
    function c() external { .. }
}
```

still a bit work in progress; use with function inliner to merge constructors, etc.

## renaming identifiers

rename identifier to avoid shadowing identifiers.

besides debugging it is also useful to when inlining internal functions.

example:
```py
from mutators import mark_identifiers
mark_identifiers.rename_all(ast)
```

input:
```solidity
address owner;
uint256 balance;
```

output:
```solidity
address owner_1;
uint256 balance_2;
```

## storage relocator

(work in progress)

```py
from mutators import storage_relocator
storage_relocator.patch_storage_slots(ast)
```

## simplifier

remove non-required nodes from AST. useful for debugging to reduce information clutter.

```py
from mutators import simplify
simplify.simplify(ast)
```

