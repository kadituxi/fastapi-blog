### Migrations using Alembic
- uv run alembic init -t async alembic
- Add on env.py: config.set_main_option("sqlalchemy.url", settings.database_url)
- Set on env.py: target_metadata = Base.metadata
- Delete demo url from alembic.ini: sqlalchemy.url = 
- uv run alembic revision --autogenerate -m "initial schema"
- uv run alembic upgrade head
- uv run alembic current
- alembic downgrade -2
- uv run alembic history