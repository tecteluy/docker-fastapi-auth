"""Revised unit tests for backup_login endpoint."""
import os
import json
import pytest
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.routes.auth import backup_login, BackupLoginRequest
from app.models.user import User

@ pytest.mark.asyncio
async def test_backup_login_success_create_user():
    """Test successful backup login creating a new user."""
    mock_db = Mock(spec=Session)
    # User does not exist
    mock_db.query.return_value.filter.return_value.first.return_value = None
    mock_db.add.return_value = None
    mock_db.commit.return_value = None
    mock_db.refresh.return_value = None

    users_config = {
        'admin': {
            'password_hash': '6fec2a9601d5b3581c94f2150fc07fa3d6e45808079428354b868e412b76e6bb',
            'is_admin': True,
            'permissions': {'services': ['*']}
        }
    }
    with patch.dict(os.environ, {'BACKUP_USERS': json.dumps(users_config)}):
        with patch('app.routes.auth.auth_service') as mock_auth:
            mock_auth.create_tokens.return_value = {
                'access_token': 'token',
                'refresh_token': 'refresh',
                'token_type': 'bearer',
                'expires_in': 3600
            }
            request = BackupLoginRequest(username='admin', password='test12345')
            response = await backup_login(request, mock_db)

            assert response['access_token'] == 'token'
            assert response['user']['username'] == 'backup_admin'
            mock_db.add.assert_called_once()

@ pytest.mark.asyncio
async def test_backup_login_existing_user_no_create():
    """Test backup login when user exists in database."""
    existing = User(id=1, email='backup@x.com', username='backup_admin',
                    full_name='Backup Admin', is_admin=True,
                    permissions={'services': ['*']})
    mock_db = Mock(spec=Session)
    mock_db.query.return_value.filter.return_value.first.return_value = existing

    users_config = {
        'admin': {
            'password_hash': '6fec2a9601d5b3581c94f2150fc07fa3d6e45808079428354b868e412b76e6bb',
            'is_admin': True,
            'permissions': {'services': ['*']}
        }
    }
    with patch.dict(os.environ, {'BACKUP_USERS': json.dumps(users_config)}):
        with patch('app.routes.auth.auth_service') as mock_auth:
            mock_auth.create_tokens.return_value = {
                'access_token': 'token',
                'refresh_token': 'refresh',
                'token_type': 'bearer',
                'expires_in': 3600
            }
            request = BackupLoginRequest(username='admin', password='test12345')
            response = await backup_login(request, mock_db)

            mock_db.add.assert_not_called()
            assert response['user']['username'] == 'backup_admin'

@ pytest.mark.asyncio
async def test_backup_login_wrong_password():
    """Test backup login with incorrect password."""
    mock_db = Mock(spec=Session)
    users_config = {'admin': {'password_hash': 'wronghash', 'is_admin': True, 'permissions': {}}}
    with patch.dict(os.environ, {'BACKUP_USERS': json.dumps(users_config)}):
        request = BackupLoginRequest(username='admin', password='test12345')
        with pytest.raises(HTTPException) as exc:
            await backup_login(request, mock_db)
        assert exc.value.status_code == 401

@ pytest.mark.asyncio
async def test_backup_login_missing_user():
    """Test backup login with missing username."""
    mock_db = Mock(spec=Session)
    users_config = {'admin': {'password_hash': 'hash', 'is_admin': True, 'permissions': {}}}
    with patch.dict(os.environ, {'BACKUP_USERS': json.dumps(users_config)}):
        request = BackupLoginRequest(username='unknown', password='test12345')
        with pytest.raises(HTTPException) as exc:
            await backup_login(request, mock_db)
        assert exc.value.status_code == 401

@ pytest.mark.asyncio
async def test_backup_login_no_configuration():
    """Test backup login with no configuration."""
    mock_db = Mock(spec=Session)
    request = BackupLoginRequest(username='admin', password='test12345')
    with pytest.raises(HTTPException) as exc:
        await backup_login(request, mock_db)
    assert exc.value.status_code == 503

@ pytest.mark.asyncio
async def test_backup_login_invalid_json():
    """Test backup login with invalid JSON config."""
    mock_db = Mock(spec=Session)
    with patch.dict(os.environ, {'BACKUP_USERS': 'not-json'}):
        request = BackupLoginRequest(username='admin', password='test12345')
        with pytest.raises(HTTPException) as exc:
            await backup_login(request, mock_db)
        assert exc.value.status_code == 500
