param(
  [string]$Bootstrap = "kafka:9092"
)

docker exec -e KAFKA_BOOTSTRAP=$Bootstrap crypto-kafka bash -lc "bash /tmp/create-topics.sh"