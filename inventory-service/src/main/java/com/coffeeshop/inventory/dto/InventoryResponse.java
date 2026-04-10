package com.coffeeshop.inventory.dto;

import com.coffeeshop.inventory.model.InventoryItem;

import java.util.UUID;

public record InventoryResponse(
        UUID id,
        UUID productId,
        int quantity,
        int reserved,
        int availableStock
) {
    public static InventoryResponse from(InventoryItem item) {
        return new InventoryResponse(
                item.getId(),
                item.getProductId(),
                item.getQuantity(),
                item.getReserved(),
                item.availableStock()
        );
    }
}
