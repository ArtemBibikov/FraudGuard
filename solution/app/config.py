import os

class Settings:
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = int(os.getenv("DB_PORT", "5432"))
    DB_NAME = os.getenv("DB_NAME", "testdb")
    DB_USER = os.getenv("DB_USER", "postgres")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")

    REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))

    ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@mail.ru")
    ADMIN_FULLNAME = os.getenv("ADMIN_FULLNAME", "Test Test")
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "123123123aA!")

    RANDOM_SECRET = os.getenv(
        "RANDOM_SECRET",
        "Jf/ZpZSxfMWnOexP48Mp1z200jd+8BVZ7ws6Uw5Jp/w="
    )
    SECRET_KEY = RANDOM_SECRET
    JWT_ALGORITHM = "HS256"
    JWT_EXPIRE_MINUTES = 60
    JWT_EXPIRE_SECONDS = 3600

    @property
    def DATABASE_URL(self):
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

settings = Settings()