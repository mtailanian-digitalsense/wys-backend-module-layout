echo "Redis url: "$REDIS_URL
rq worker --url $REDIS_URL
