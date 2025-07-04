#!/usr/bin/env python3
"""Debug Redis metadata storage issue."""

import redis

from app.config import settings


def debug_redis():
    # Connect to Redis (synchronous client for debugging)
    redis_client = redis.Redis.from_url(settings.redis_url, decode_responses=True)

    print("🔍 Redis Debug Information:")
    print(f"Redis URL: {settings.redis_url}")

    try:
        # Test Redis connection
        redis_client.ping()
        print("✅ Redis connection successful")

        # Get all keys
        all_keys = redis_client.keys("*")
        print(f"📋 All Redis keys: {all_keys}")

        # Check task list
        task_list = redis_client.lrange("celery_tasks", 0, -1)
        print(f"📋 Task list: {task_list}")

        # Check metadata for each task
        for task_id in task_list:
            metadata_key = f"task_metadata:{task_id}"
            metadata = redis_client.hgetall(metadata_key)
            print(f"📋 Metadata for {task_id}: {metadata}")

            # Check if key exists and TTL
            exists = redis_client.exists(metadata_key)
            ttl = redis_client.ttl(metadata_key)
            print(f"📋 Key exists: {exists}, TTL: {ttl}")

    except Exception as e:
        print(f"❌ Redis error: {e}")


if __name__ == "__main__":
    debug_redis()
