"""Tests for database module."""

import pytest
from sqlalchemy import select

from src.persistence.database import (
    Database,
    Base,
    SyncRecordModel,
    SyncStatusEnum,
    get_db,
)


@pytest.fixture
async def test_db():
    """Create a test database in memory."""
    db = Database(database_url="sqlite+aiosqlite:///:memory:")
    await db.init_db()
    yield db
    await db.close()


class TestSyncStatusEnum:
    """Tests for SyncStatusEnum."""

    def test_enum_values(self):
        """Test all enum values exist."""
        assert SyncStatusEnum.PENDING == "pending"
        assert SyncStatusEnum.TRANSLATED == "translated"
        assert SyncStatusEnum.PUBLISHED_XHS == "published_xhs"
        assert SyncStatusEnum.PUBLISHED_WECHAT == "published_wechat"
        assert SyncStatusEnum.PUBLISHED_ALL == "published_all"
        assert SyncStatusEnum.FAILED == "failed"


class TestDatabase:
    """Tests for Database class."""

    async def test_init_db_creates_tables(self, test_db):
        """Test that init_db creates all tables."""
        # Try to insert a record - this will fail if table doesn't exist
        async with test_db.session() as session:
            record = SyncRecordModel(
                tweet_id="test123",
                author_id="author123",
                original_text="Hello world",
                status=SyncStatusEnum.PENDING,
            )
            session.add(record)

        # Verify record was created
        async with test_db.session() as session:
            result = await session.execute(
                select(SyncRecordModel).where(SyncRecordModel.tweet_id == "test123")
            )
            found = result.scalar_one_or_none()
            assert found is not None
            assert found.tweet_id == "test123"

    async def test_session_commit(self, test_db):
        """Test that session commits on success."""
        async with test_db.session() as session:
            record = SyncRecordModel(
                tweet_id="commit_test",
                author_id="author",
                original_text="Test",
            )
            session.add(record)

        # Verify in a new session
        async with test_db.session() as session:
            result = await session.execute(
                select(SyncRecordModel).where(SyncRecordModel.tweet_id == "commit_test")
            )
            assert result.scalar_one_or_none() is not None

    async def test_session_rollback_on_error(self, test_db):
        """Test that session rolls back on error."""
        try:
            async with test_db.session() as session:
                record = SyncRecordModel(
                    tweet_id="rollback_test",
                    author_id="author",
                    original_text="Test",
                )
                session.add(record)
                raise ValueError("Simulated error")
        except ValueError:
            pass

        # Verify record was not created
        async with test_db.session() as session:
            result = await session.execute(
                select(SyncRecordModel).where(SyncRecordModel.tweet_id == "rollback_test")
            )
            assert result.scalar_one_or_none() is None


class TestSyncRecordModel:
    """Tests for SyncRecordModel."""

    async def test_create_record(self, test_db):
        """Test creating a sync record."""
        async with test_db.session() as session:
            record = SyncRecordModel(
                tweet_id="tweet_1",
                author_id="author_1",
                original_text="Original text",
                translated_text="翻译文本",
                status=SyncStatusEnum.TRANSLATED,
            )
            session.add(record)

        async with test_db.session() as session:
            result = await session.execute(
                select(SyncRecordModel).where(SyncRecordModel.tweet_id == "tweet_1")
            )
            record = result.scalar_one()
            assert record.original_text == "Original text"
            assert record.translated_text == "翻译文本"
            assert record.status == SyncStatusEnum.TRANSLATED

    async def test_unique_tweet_id(self, test_db):
        """Test that tweet_id is unique."""
        async with test_db.session() as session:
            record1 = SyncRecordModel(
                tweet_id="unique_id",
                author_id="author",
                original_text="First",
            )
            session.add(record1)

        # Trying to add duplicate should fail
        with pytest.raises(Exception):
            async with test_db.session() as session:
                record2 = SyncRecordModel(
                    tweet_id="unique_id",
                    author_id="author",
                    original_text="Second",
                )
                session.add(record2)

    async def test_default_status(self, test_db):
        """Test default status is PENDING."""
        async with test_db.session() as session:
            record = SyncRecordModel(
                tweet_id="default_status",
                author_id="author",
                original_text="Test",
            )
            session.add(record)

        async with test_db.session() as session:
            result = await session.execute(
                select(SyncRecordModel).where(SyncRecordModel.tweet_id == "default_status")
            )
            record = result.scalar_one()
            assert record.status == SyncStatusEnum.PENDING

    async def test_nullable_fields(self, test_db):
        """Test nullable fields can be null."""
        async with test_db.session() as session:
            record = SyncRecordModel(
                tweet_id="nullable_test",
                author_id="author",
                original_text="Test",
            )
            session.add(record)

        async with test_db.session() as session:
            result = await session.execute(
                select(SyncRecordModel).where(SyncRecordModel.tweet_id == "nullable_test")
            )
            record = result.scalar_one()
            assert record.translated_text is None
            assert record.xhs_post_id is None
            assert record.wechat_article_id is None
            assert record.error_message is None


class TestGetDb:
    """Tests for get_db function."""

    def test_get_db_returns_database(self):
        """Test get_db returns a Database instance."""
        # Reset global state
        import src.persistence.database as db_module
        db_module._db = None

        db = get_db()
        assert isinstance(db, Database)

    def test_get_db_singleton(self):
        """Test get_db returns the same instance."""
        import src.persistence.database as db_module
        db_module._db = None

        db1 = get_db()
        db2 = get_db()
        assert db1 is db2
