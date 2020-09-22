"""Sets up the redis connection and the redis queue."""
import os

import redis
from rq import Queue

redis_conn = redis.Redis(
    host=os.getenv("REDIS_HOST", "10.2.19.195"),
    port=os.getenv("REDIS_PORT", "6379"),
    password=os.getenv("REDIS_PASSWORD", ""),
)

redis_queue = Queue(connection=redis_conn,timeout=1000)