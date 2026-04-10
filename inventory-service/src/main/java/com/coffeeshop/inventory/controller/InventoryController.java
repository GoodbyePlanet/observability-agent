package com.coffeeshop.inventory.controller;

import com.coffeeshop.inventory.dto.*;
import com.coffeeshop.inventory.service.InventoryService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.*;

import java.util.UUID;

@RestController
@RequestMapping("/api/inventory")
@RequiredArgsConstructor
public class InventoryController {

    private final InventoryService inventoryService;

    @GetMapping("/{productId}")
    public InventoryResponse getStock(@PathVariable UUID productId) {
        return inventoryService.getByProductId(productId);
    }

    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    public InventoryResponse add(@RequestBody AddInventoryRequest request) {
        return inventoryService.add(request);
    }

    @PostMapping("/{productId}/reserve")
    public ReservationResponse reserve(@PathVariable UUID productId,
                                       @RequestBody ReserveStockRequest request) {
        return inventoryService.reserve(productId, request);
    }

    @PutMapping("/{productId}")
    public InventoryResponse updateQuantity(@PathVariable UUID productId,
                                            @RequestParam int quantity) {
        return inventoryService.updateQuantity(productId, quantity);
    }
}
