# Prontivus Database User & Permission Queries

## Quick Database Access

### Connect to Database
```bash
# Using psql (if you have direct access)
psql "postgresql://prontivus_rh0l_user:eKdELoiPkpuvqiuD84ao7yfkltPy7oev@dpg-d39ab7fdiees7387nihg-a.oregon-postgres.render.com/prontivus_rh0l"

# Or use the Python script
cd backend
python check_users_and_permissions.py
```

## Essential SQL Queries

### 1. Check All Users
```sql
SELECT 
    id, email, username, full_name, cpf, crm,
    is_active, is_verified, is_superuser,
    created_at, last_login
FROM users 
ORDER BY id;
```

### 2. Check User Roles
```sql
SELECT 
    u.id, u.email, u.full_name,
    r.name as role_name, r.description, r.permissions
FROM users u
LEFT JOIN user_roles ur ON u.id = ur.user_id
LEFT JOIN roles r ON ur.role_id = r.id
ORDER BY u.id, r.name;
```

### 3. Check Specific User Permissions
```sql
-- Replace 'admin@prontivus.com' with the user email you want to check
SELECT 
    u.id, u.email, u.full_name, u.is_superuser,
    r.name as role_name, r.permissions
FROM users u
LEFT JOIN user_roles ur ON u.id = ur.user_id
LEFT JOIN roles r ON ur.role_id = r.id
WHERE u.email = 'admin@prontivus.com';
```

### 4. Check All Available Roles
```sql
SELECT id, name, description, permissions, created_at
FROM roles 
ORDER BY id;
```

### 5. Check User-Role Assignments
```sql
SELECT 
    u.id, u.email, u.full_name, 
    r.name as role_name, ur.created_at
FROM user_roles ur
JOIN users u ON ur.user_id = u.id
JOIN roles r ON ur.role_id = r.id
ORDER BY u.id, r.name;
```

### 6. Check Active Users Only
```sql
SELECT 
    id, email, full_name, is_active, last_login
FROM users 
WHERE is_active = true
ORDER BY last_login DESC;
```

### 7. Check Users Without Roles (Patients)
```sql
SELECT 
    u.id, u.email, u.full_name, u.cpf
FROM users u
LEFT JOIN user_roles ur ON u.id = ur.user_id
WHERE ur.user_id IS NULL;
```

## Default Users & Credentials

| Email | Password | Role | Type | Description |
|-------|-----------|------|------|-------------|
| admin@prontivus.com | admin123 | admin | staff | System Administrator |
| doctor@prontivus.com | doctor123 | doctor | staff | Medical Doctor |
| secretary@prontivus.com | secretary123 | secretary | staff | Secretary/Receptionist |
| patient@prontivus.com | patient123 | patient | patient | Patient User |

## Permission System

### Role-Based Access Control (RBAC)

The system uses a **Role-Based Access Control** model:

1. **Users** (`users` table) - Contains user information
2. **Roles** (`roles` table) - Contains role definitions with permissions
3. **User-Role Assignments** (`user_roles` table) - Links users to roles

### Permission Structure

Permissions are stored as JSON arrays in the `roles.permissions` column:

```json
{
  "admin": ["*"],  // Full access
  "doctor": [
    "patients:read", "patients:update",
    "appointments:create", "appointments:read", "appointments:update",
    "medical_records:create", "medical_records:read", "medical_records:update",
    "prescriptions:create", "prescriptions:read", "prescriptions:update",
    "reports:read"
  ],
  "secretary": [
    "patients:create", "patients:read", "patients:update",
    "appointments:create", "appointments:read", "appointments:update", "appointments:delete",
    "reports:read"
  ],
  "patient": [
    "own_data:read",
    "appointments:read",
    "prescriptions:read"
  ]
}
```

### User Types

- **Staff Users**: Have roles assigned, access staff features
- **Patient Users**: No roles assigned, limited to own data

### Permission Checking Logic

1. **Frontend**: Uses `RoleGuard` component to check user type and role
2. **Backend**: Uses authentication dependencies to verify permissions
3. **Database**: Queries `user_roles` table to determine user permissions

## Troubleshooting

### Common Issues

1. **User can't login**: Check `is_active` and `is_verified` flags
2. **User has no permissions**: Check if user has roles in `user_roles` table
3. **Wrong user type**: Check if user has roles (staff) or not (patient)

### Quick Fixes

```sql
-- Activate a user
UPDATE users SET is_active = true WHERE email = 'user@example.com';

-- Assign admin role to a user
INSERT INTO user_roles (user_id, role_id, tenant_id, created_at)
SELECT u.id, r.id, u.tenant_id, NOW()
FROM users u, roles r
WHERE u.email = 'user@example.com' AND r.name = 'admin';

-- Check if tables exist
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN ('users', 'roles', 'user_roles');
```

## API Endpoints for User Management

- `GET /api/v1/users` - List all users
- `GET /api/v1/auth/me` - Get current user info
- `POST /api/v1/user-lookup/lookup` - Check user type before login
- `POST /api/v1/database/create-tables` - Create missing tables
