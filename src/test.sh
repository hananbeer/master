while true
do
    python ./src/ast_patcher.py | jq . > ./data/embed.json && sol-ast-compile --source ./data/embed.json > ./data/live.tmp.sol
    cp ./data/live.tmp.sol ./data/live.sol
    sleep 5
done
