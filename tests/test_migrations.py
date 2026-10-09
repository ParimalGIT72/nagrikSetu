from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import inspect, text

BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"


def test_auth_migration_downgrade_preserves_legacy_tables_and_rows(test_engine):
    config = Config(str(BACKEND_DIR / "alembic.ini"))
    with test_engine.connect() as connection:
        config.attributes["connection"] = connection
        complaint_count_before = connection.execute(
            text("SELECT count(*) FROM complaints")
        ).scalar_one()
        preprocessing_count_before = connection.execute(
            text("SELECT count(*) FROM complaint_preprocessing")
        ).scalar_one()
        connection.commit()

        try:
            command.downgrade(config, "-1")
            connection.commit()
            inspector = inspect(connection)
            assert "users" not in inspector.get_table_names()
            assert "user_id" not in {
                column["name"] for column in inspector.get_columns("complaints")
            }
            assert "complaint_preprocessing" in inspector.get_table_names()
            complaint_count_after = connection.execute(
                text("SELECT count(*) FROM complaints")
            ).scalar_one()
            preprocessing_count_after = connection.execute(
                text("SELECT count(*) FROM complaint_preprocessing")
            ).scalar_one()
            connection.commit()
            assert complaint_count_after == complaint_count_before
            assert preprocessing_count_after == preprocessing_count_before
        finally:
            command.upgrade(config, "head")
            connection.commit()
            config.attributes.pop("connection", None)

        inspector = inspect(connection)
        assert "users" in inspector.get_table_names()
        assert "user_id" in {
            column["name"] for column in inspector.get_columns("complaints")
        }