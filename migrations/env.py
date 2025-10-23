from __future__ import annotations
from logging.config import fileConfig
import os
from urllib.parse import quote_plus

from sqlalchemy import engine_from_config, pool, create_engine
from alembic import context


# تحميل .env
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass


from app.infra.db.database import Base
from app.infra.db import models  # noqa: F401


config = context.config


# بناء الـ URL مع encoding
db_url = os.getenv("DATABASE_URL")
if not db_url:
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "5432")
    name = os.getenv("DB_NAME", "postgres")
    user = quote_plus(os.getenv("DB_USER", "postgres"))
    pw   = quote_plus(os.getenv("DB_PASSWORD", ""))
    db_url = f"postgresql+psycopg2://{user}:{pw}@{host}:{port}/{name}?sslmode=require"


# ✅ لا نستخدم config.set_main_option لتجنب مشاكل ConfigParser مع الرموز الخاصة


if config.config_file_name is not None:
    fileConfig(config.config_file_name)


target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    context.configure(
        url=db_url,  # استخدام المتغير مباشرة
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    # ✅ بناء الـ engine مباشرة بدلاً من engine_from_config
    connectable = create_engine(
        db_url,
        poolclass=pool.NullPool,
    )
    
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
