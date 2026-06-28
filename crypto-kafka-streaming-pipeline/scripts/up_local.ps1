Write-Host "Starting Kafka..." -ForegroundColor Yellow
docker compose -f docker\compose.yml up -d

Write-Host "Creating topics..." -ForegroundColor Yellow
docker cp docker\kafka\create-topics.sh crypto-kafka:/tmp/create-topics.sh | Out-Null
docker exec crypto-kafka bash -lc "bash /tmp/create-topics.sh" | Out-Host

Write-Host "✅ Kafka up and topics ensured." -ForegroundColor Green