INSERT INTO products (id, name, description, price, category, created_at, updated_at) VALUES
  ('11111111-1111-1111-1111-111111111111', 'Espresso',     'Rich, bold shot of pure coffee',             3.50, 'espresso',  NOW(), NOW()),
  ('22222222-2222-2222-2222-222222222222', 'Cappuccino',   'Espresso with steamed milk foam',            4.50, 'milk-based',NOW(), NOW()),
  ('33333333-3333-3333-3333-333333333333', 'Latte',        'Espresso with lots of steamed milk',         4.75, 'milk-based',NOW(), NOW()),
  ('44444444-4444-4444-4444-444444444444', 'Cold Brew',    'Slow-steeped cold coffee, smooth and strong',5.00, 'cold',      NOW(), NOW()),
  ('55555555-5555-5555-5555-555555555555', 'Matcha Latte', 'Ceremonial grade matcha with oat milk',      5.50, 'specialty', NOW(), NOW())
ON CONFLICT (id) DO NOTHING;
