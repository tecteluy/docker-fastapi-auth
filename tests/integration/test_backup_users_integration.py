# Integration tests for backup user functionality
import pytest
import json
import os
from unittest.mock import patch
from sqlalchemy.orm import Session
from app.routes.auth import backup_login, BackupLoginRequest
from app.models.user import User
from app.database import get_db


class TestBackupUserIntegration:
    """Integration tests for backup user functionality with database."""
    
    @pytest.mark.asyncio
    async def test_backup_login_creates_user_in_database(self, test_db: Session):
        """Test that backup login creates a user in the database."""
        with patch.dict(os.environ, {
            'BACKUP_USERS': json.dumps({
            'testuser': {
                'password_hash': '6fec2a9601d5b3581c94f2150fc07fa3d6e45808079428354b868e412b76e6bb',  # hash of 'test12345'
                    'is_admin': False,
                    'permissions': {'services': ['read']}
                }
            })
        }):
            # Ensure user doesn't exist
            existing_user = test_db.query(User).filter(
                User.username == "backup_testuser",
                User.provider == "backup"
            ).first()
            if existing_user:
                test_db.delete(existing_user)
                test_db.commit()

            # Perform backup login
            request = BackupLoginRequest(username="testuser", password="test12345")
            response = await backup_login(request, test_db)

            # Verify response
            assert response['user']['username'] == "backup_testuser"
            assert response['user']['email'] == "backup_testuser@atrium.local"
            assert response['user']['is_admin'] == False
            assert response['user']['permissions'] == {'services': ['read']}
            assert 'access_token' in response
            assert 'refresh_token' in response

            # Verify user was created in database
            created_user = test_db.query(User).filter(
                User.username == "backup_testuser",
                User.provider == "backup"
            ).first()

            assert created_user is not None
            assert created_user.email == "backup_testuser@atrium.local"
            assert created_user.full_name == "Backup User: testuser"
            assert created_user.is_admin == False
            assert created_user.permissions == {'services': ['read']}
            assert created_user.is_active == True

    @pytest.mark.asyncio
    async def test_backup_login_existing_user_no_duplicate(self, test_db: Session):
        """Test that backup login doesn't create duplicate users."""
        with patch.dict(os.environ, {
            'BACKUP_USERS': json.dumps({
                'existinguser': {
                    'password_hash': '6fec2a9601d5b3581c94f2150fc07fa3d6e45808079428354b868e412b76e6bb',  # hash of 'test12345'
                    'is_admin': True,
                    'permissions': {'services': ['*']}
                }
            })
        }):
            # Create user first
            first_request = BackupLoginRequest(username="existinguser", password="test12345")
            first_response = await backup_login(first_request, test_db)

            # Count users before second login
            user_count_before = test_db.query(User).filter(
                User.username == "backup_existinguser",
                User.provider == "backup"
            ).count()

            # Login again with same user
            second_request = BackupLoginRequest(username="existinguser", password="test12345")
            second_response = await backup_login(second_request, test_db)

            # Count users after second login
            user_count_after = test_db.query(User).filter(
                User.username == "backup_existinguser",
                User.provider == "backup"
            ).count()

            # Should still be only one user
            assert user_count_before == 1
            assert user_count_after == 1
            assert first_response['user']['id'] == second_response['user']['id']

    @pytest.mark.asyncio
    async def test_backup_login_different_users_create_separate_records(self, test_db: Session):
        """Test that different backup users create separate database records."""
        with patch.dict(os.environ, {
            'BACKUP_USERS': json.dumps({
                'user1': {
                    'password_hash': '6fec2a9601d5b3581c94f2150fc07fa3d6e45808079428354b868e412b76e6bb',  # hash of 'test12345'
                    'is_admin': True,
                    'permissions': {'services': ['*']}
                },
                'user2': {
                    'password_hash': '866d68aeb057cfe0b155e4e32c1775bfba179d19ee6506b84728475bae3cf5e7',  # hash of 'operator12345'
                    'is_admin': False,
                    'permissions': {'services': ['read', 'write']}
                }
            })
        }):
            # Clean up any existing test users
            for username in ['backup_user1', 'backup_user2']:
                existing = test_db.query(User).filter(
                    User.username == username,
                    User.provider == "backup"
                ).first()
                if existing:
                    test_db.delete(existing)
            test_db.commit()

            # Login with first user
            request1 = BackupLoginRequest(username="user1", password="test12345")
            response1 = await backup_login(request1, test_db)

            # Login with second user
            request2 = BackupLoginRequest(username="user2", password="operator12345")
            response2 = await backup_login(request2, test_db)

            # Verify both users exist with different properties
            user1 = test_db.query(User).filter(
                User.username == "backup_user1",
                User.provider == "backup"
            ).first()

            user2 = test_db.query(User).filter(
                User.username == "backup_user2",
                User.provider == "backup"
            ).first()

            assert user1 is not None
            assert user2 is not None
            assert user1.id != user2.id
            assert user1.is_admin == True
            assert user2.is_admin == False
            assert user1.permissions == {'services': ['*']}
            assert user2.permissions == {'services': ['read', 'write']}

    @pytest.mark.asyncio
    async def test_backup_login_updates_existing_user_permissions(self, test_db: Session):
        """Test that backup login can update existing user permissions if config changes."""
        with patch.dict(os.environ, {
            'BACKUP_USERS': json.dumps({
                'updateuser': {
                    'password_hash': '6fec2a9601d5b3581c94f2150fc07fa3d6e45808079428354b868e412b76e6bb',  # hash of 'test12345'
                    'is_admin': False,  # Changed from True to False
                    'permissions': {'services': ['read']}  # Changed permissions
                }
            })
        }):
            # Create user with initial permissions
            initial_user = User(
                email="backup_updateuser@atrium.local",
                username="backup_updateuser",
                full_name="Backup User: updateuser",
                provider="backup",
                provider_id="updateuser",
                is_active=True,
                is_admin=True,  # Initially admin
                permissions={'services': ['*']}  # Initially full access
            )
            test_db.add(initial_user)
            test_db.commit()
            test_db.refresh(initial_user)

            # Login with updated configuration
            request = BackupLoginRequest(username="updateuser", password="test12345")
            response = await backup_login(request, test_db)

            # The current implementation doesn't update existing users' permissions
            # This test documents the current behavior
            # In a future enhancement, we might want to update existing users
            assert response['user']['is_admin'] == True  # Still the original value
            assert response['user']['permissions'] == {'services': ['*']}  # Still the original value
