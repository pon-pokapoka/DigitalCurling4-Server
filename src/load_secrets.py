import os
from dotenv import load_dotenv

load_dotenv()

user = os.getenv("DB_USER")
password = os.getenv("DB_PASSWORD")
host = os.getenv("DB_HOST")
port = os.getenv("DB_PORT")
db_name = os.getenv("DB_NAME")
pepper_data = os.getenv("PEPPER_DATA")

# Each process opens up to pool_size + max_overflow connections, so keep the
# total across replicas below Postgres's max_connections.
db_pool_size = int(os.getenv("DB_POOL_SIZE", "20"))
db_max_overflow = int(os.getenv("DB_MAX_OVERFLOW", "20"))

redis_host = os.getenv("REDIS_HOST", "redis")
redis_port = int(os.getenv("REDIS_PORT", "6379"))
