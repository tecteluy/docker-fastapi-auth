#!/usr/bin/env python3

import re

# Read the test file
with open('tests/unit/test_backup_users.py', 'r') as f:
    content = f.read()

# Fix all test methods to be async
content = re.sub(r'(\s+)def (test_backup_[^(]+\([^)]*\):)', r'\1@pytest.mark.asyncio\n\1async def \2', content)

# Fix all backup_login calls to be awaited
content = re.sub(r'(\s+)(response = backup_login\([^)]+\))', r'\1\2\n\1response = await backup_login(request, mock_db)', content)
content = re.sub(r'(\s+)(backup_login\(request, mock_db\))', r'\1await \2', content)

# Remove duplicate await calls
content = re.sub(r'response = await backup_login\([^)]+\)\s+response = await backup_login\([^)]+\)', 'response = await backup_login(request, mock_db)', content)

# Write back
with open('tests/unit/test_backup_users.py', 'w') as f:
    f.write(content)

print("Fixed async issues in backup user tests")
