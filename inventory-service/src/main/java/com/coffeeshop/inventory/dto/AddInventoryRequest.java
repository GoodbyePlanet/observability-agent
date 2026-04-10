package com.coffeeshop.inventory.dto;

import java.util.UUID;

public record AddInventoryRequest(UUID productId, int quantity) {}
