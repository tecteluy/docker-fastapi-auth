# OAuth Service for Multiple Applications

The OAuth service now supports dynamic redirect URLs for different client applications.

## Usage Examples

### Example 1: Web Application (www-tectel-com-uy)
```javascript
// Frontend signin page
const handleOAuthLogin = async (provider) => {
  const authUrl = `${AUTH_API_URL}/login/${provider}?client_redirect_uri=${encodeURIComponent('https://devel.tectel.uy/signin?success=true')}`;
  const response = await fetch(authUrl);
  const data = await response.json();
  if (data.auth_url) {
    window.location.href = data.auth_url;
  }
};
```

### Example 2: Admin Dashboard
```javascript
// Admin dashboard signin
const handleOAuthLogin = async (provider) => {
  const authUrl = `${AUTH_API_URL}/login/${provider}?client_redirect_uri=${encodeURIComponent('https://admin.tectel.uy/dashboard?auth=success')}`;
  const response = await fetch(authUrl);
  const data = await response.json();
  if (data.auth_url) {
    window.location.href = data.auth_url;
  }
};
```

### Example 3: Mobile App Callback
```javascript
// Mobile app callback URL
const handleOAuthLogin = async (provider) => {
  const authUrl = `${AUTH_API_URL}/login/${provider}?client_redirect_uri=${encodeURIComponent('myapp://auth/callback?success=true')}`;
  const response = await fetch(authUrl);
  const data = await response.json();
  if (data.auth_url) {
    window.location.href = data.auth_url;
  }
};
```

### Example 4: API Service Integration
```javascript
// API service with token handling
const handleOAuthLogin = async (provider) => {
  const authUrl = `${AUTH_API_URL}/login/${provider}?client_redirect_uri=${encodeURIComponent('https://api.tectel.uy/auth/tokens')}`;
  const response = await fetch(authUrl);
  const data = await response.json();
  if (data.auth_url) {
    window.location.href = data.auth_url;
  }
};
```

## Parameters

- `client_redirect_uri` (optional): The final URL where users should be redirected after successful authentication
  - If not provided, defaults to `${settings.frontend_url}/signin?success=true`
  - On success: redirects to the exact URL provided
  - On error: adds `?error=oauth_failed` or `&error=oauth_failed` to the URL

## Security Considerations

1. **Allowed Redirect URIs**: Consider implementing a whitelist of allowed redirect URIs in production
2. **HTTPS Only**: Ensure all redirect URIs use HTTPS in production
3. **Domain Validation**: Validate that redirect URIs belong to trusted domains

## Implementation Notes

- The OAuth service maintains backward compatibility with the old format
- State parameter format: `state:oauth_redirect_uri:client_redirect_uri:provider`
- Error handling preserves query parameters in the client redirect URI