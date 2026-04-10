package com.coffeeshop.order.client.dto;

public record ReservationResponse(boolean success, int availableStock, String message) {}
