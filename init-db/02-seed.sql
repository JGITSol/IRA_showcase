-- Create a default admin user if it doesn't exist
-- Password is 'admin123' (hashed with bcrypt)
INSERT INTO users (email, hashed_password, full_name, is_active, is_superuser, role)
VALUES (
    'admin@example.com',
    '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW',  -- bcrypt for 'admin123'
    'Admin User',
    true,
    true,
    'superuser'
)
ON CONFLICT (email) DO NOTHING;

-- Create a test user if it doesn't exist
-- Password is 'test123' (hashed with bcrypt)
INSERT INTO users (email, hashed_password, full_name, is_active, role)
VALUES (
    'user@example.com',
    '$2b$12$G9fqO95VLh0pU.3fRfB9FeqfJzLg2uV2QZQJxY9XKvZGkq1lZzQbC',  -- bcrypt for 'test123'
    'Test User',
    true,
    'user'
)
ON CONFLICT (email) DO NOTHING;

-- Create some test predictions for the test user
WITH inserted_user AS (
    SELECT id FROM users WHERE email = 'user@example.com'
)
INSERT INTO predictions (user_id, status, input_data, prediction_result, confidence)
SELECT 
    id,
    'completed',
    '{"age": 35, "bmi": 28.5, "children": 2, "smoker": false, "region": "northeast"}'::jsonb,
    '{"predicted_charges": 9876.54}'::jsonb,
    0.85
FROM inserted_user
WHERE NOT EXISTS (SELECT 1 FROM predictions LIMIT 1);

-- Create a refresh token for the admin user
WITH inserted_user AS (
    SELECT id FROM users WHERE email = 'admin@example.com'
)
INSERT INTO refresh_tokens (user_id, token, expires_at)
SELECT 
    id,
    'admin_refresh_token_123456',
    NOW() + INTERVAL '30 days'
FROM inserted_user
WHERE NOT EXISTS (SELECT 1 FROM refresh_tokens WHERE token = 'admin_refresh_token_123456');

-- Create a refresh token for the test user
WITH inserted_user AS (
    SELECT id FROM users WHERE email = 'user@example.com'
)
INSERT INTO refresh_tokens (user_id, token, expires_at)
SELECT 
    id,
    'user_refresh_token_123456',
    NOW() + INTERVAL '30 days'
FROM inserted_user
WHERE NOT EXISTS (SELECT 1 FROM refresh_tokens WHERE token = 'user_refresh_token_123456');
