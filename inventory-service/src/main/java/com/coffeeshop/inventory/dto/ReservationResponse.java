package com.coffeeshop.inventory.dto;

public record ReservationResponse(boolean success, int availableStock, String message) {}
