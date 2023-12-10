while true
do
    python ./src/ast_patcher.py | jq . > ./data/live.json && sol-ast-compile --source ./data/live.json > ./data/live.tmp.sol
    cp ./data/live.tmp.sol ./data/live.sol
    echo "executed."
    sleep 5
done
