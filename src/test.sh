while true
do
    python ./src/ast_patcher.py | jq . > ./data/embed.json && sol-ast-compile --source ./data/embed.json > ./data/sample.tmp.sol
    cp ./data/sample.tmp.sol ./data/sample.sol
    sleep 5
done
