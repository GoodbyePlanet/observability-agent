package com.coffeeshop.order.dto;

import java.util.UUID;

public record PlaceOrderRequest(UUID productId, int quantity) {}
