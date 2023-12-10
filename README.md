# MASTER

Modify ASTs Easily & Reliably


# Install

install `sol-ast-compile` tool:

```
npm install -g solc-typed-ast
```

# Usage

```sh
# random chosen contract to work with
# start by flattening the solidity files into a single file
forge flatten ./data/0xe34b087bf3c99e664316a15b01e5295eb3512760/src/contracts/Polygon/Bridge/Zapper_Matic_Bridge_V1.sol > ./data/flat.sol

# generate solidity AST & build info
# optional formatting with jq
solc --combined-json ast ./data/flat.sol | jq . > ./data/build.json

# <MODIFY AST HERE>

sol-ast-compile --source ./data/build.json > ./data/rebuild.sol

# optionally format the rebuilt solidity code with
forge fmt ./data/rebuild.sol > ./data/formatted.sol
```

# Notes

`solc` only preserves "doc strings" which are `/** */`

it is useful to convert `// comments` and `/* comments */` to doc strings form.

(be aware of cases such as `//` is already inside `/** */`)
