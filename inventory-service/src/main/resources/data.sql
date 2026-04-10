INSERT INTO inventory_items (id, product_id, quantity, reserved, updated_at) VALUES
  (gen_random_uuid(), '11111111-1111-1111-1111-111111111111', 100, 0, NOW()),
  (gen_random_uuid(), '22222222-2222-2222-2222-222222222222', 100, 0, NOW()),
  (gen_random_uuid(), '33333333-3333-3333-3333-333333333333', 100, 0, NOW()),
  (gen_random_uuid(), '44444444-4444-4444-4444-444444444444', 100, 0, NOW()),
  (gen_random_uuid(), '55555555-5555-5555-5555-555555555555', 100, 0, NOW())
ON CONFLICT (product_id) DO NOTHING;
