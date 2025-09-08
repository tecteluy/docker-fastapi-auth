# Integration tests for database operations
import pytest
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session
from app.models.user import User, RefreshToken
from app.database import get_db

class TestDatabaseIntegration:
    def test_user_creation_and_retrieval(self, test_db: Session):
        """Test creating and retrieving a user from database."""
        # Create a test user
        user = User(
            email="integration@example.com",
            username="integration_user",
            full_name="Integration Test User",
            provider="github",
            provider_id="integration123",
            is_active=True,
            is_admin=False
        )

        test_db.add(user)
        test_db.commit()
        test_db.refresh(user)

        # Retrieve the user
        retrieved_user = test_db.query(User).filter(User.id == user.id).first()

        assert retrieved_user is not None
        assert retrieved_user.email == "integration@example.com"
        assert retrieved_user.username == "integration_user"
        assert retrieved_user.provider == "github"
        assert retrieved_user.is_active == True

    def test_user_unique_constraints(self, test_db: Session):
        """Test unique constraints on user fields."""
        # Clean up any existing test data first
        test_db.query(User).filter(User.email.like("unique%")).delete()
        test_db.commit()
        
        # Create first user
        user1 = User(
            email="unique1@example.com",
            username="unique_user1",
            provider="github",
            provider_id="unique123"
        )
        test_db.add(user1)
        test_db.commit()

        # Try to create user with same email but different provider (should fail due to unique email constraint)
        user2 = User(
            email="unique1@example.com",  # Same email - should fail
            username="unique_user2",     # Different username
            provider="google",           # Different provider
            provider_id="unique456"
        )
        test_db.add(user2)

        with pytest.raises(Exception):  # Should raise IntegrityError for duplicate email
            test_db.commit()

        # Rollback the failed transaction
        test_db.rollback()

        # Try to create user with same username (should fail)
        user3 = User(
            email="unique2@example.com",  # Different email
            username="unique_user1",     # Same username as user1 - should fail
            provider="github",
            provider_id="different123"
        )
        test_db.add(user3)

        with pytest.raises(Exception):  # Should raise IntegrityError for duplicate username
            test_db.commit()

    def test_refresh_token_operations(self, test_db: Session):
        """Test refresh token creation and storage."""
        from datetime import datetime, timedelta
        from app.services.token_service import TokenService

        service = TokenService()

        # Create a refresh token
        token = service.create_refresh_token()
        hashed_token = service.hash_refresh_token(token)

        # Create refresh token record
        expires_at = datetime.utcnow() + timedelta(days=7)
        refresh_token = RefreshToken(
            user_id=1,
            token_hash=hashed_token,
            expires_at=expires_at,
            is_revoked=False
        )

        test_db.add(refresh_token)
        test_db.commit()
        test_db.refresh(refresh_token)

        # Retrieve and verify
        retrieved = test_db.query(RefreshToken).filter(
            RefreshToken.id == refresh_token.id
        ).first()

        assert retrieved is not None
        assert retrieved.user_id == 1
        assert retrieved.token_hash == hashed_token
        assert retrieved.is_revoked == False

    def test_database_connection_pooling(self, test_db: Session):
        """Test that database connections work properly."""
        from sqlalchemy import text
        
        # Simple query to test connection
        result = test_db.execute(text("SELECT 1 as test_value"))
        row = result.fetchone()

        assert row is not None
        assert row[0] == 1

    def test_transaction_rollback(self, test_db: Session):
        """Test transaction rollback functionality."""
        # Create a user
        user = User(
            email="rollback@example.com",
            username="rollback_user",
            provider="github",
            provider_id="rollback123"
        )

        test_db.add(user)
        test_db.commit()

        # Verify user exists
        count_before = test_db.query(User).filter(User.email == "rollback@example.com").count()
        assert count_before == 1

        # Add another user but rollback
        user2 = User(
            email="rollback2@example.com",
            username="rollback_user2",
            provider="github",
            provider_id="rollback456"
        )

        test_db.add(user2)
        test_db.rollback()  # Rollback the transaction

        # Verify second user was not persisted
        count_after = test_db.query(User).filter(User.email == "rollback2@example.com").count()
        assert count_after == 0

    @patch('app.database.SessionLocal')
    def test_get_db_generator(self, mock_session_local):
        """Test the get_db generator function for proper session management."""
        # Mock the database session
        mock_session = Mock()
        mock_session_local.return_value = mock_session
        
        # Get the generator
        gen = get_db()
        
        # Start the generator (this executes up to the yield)
        db_session = next(gen)
        
        # Verify the session was created
        assert db_session == mock_session
        mock_session_local.assert_called_once()
        
        # Simulate the generator cleanup (this executes the finally block)
        try:
            next(gen)  # This should raise StopIteration
        except StopIteration:
            pass
        
        # Verify the session was closed
        mock_session.close.assert_called_once()
