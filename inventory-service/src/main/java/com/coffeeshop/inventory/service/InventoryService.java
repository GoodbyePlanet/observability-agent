package com.coffeeshop.inventory.service;

import com.coffeeshop.inventory.dto.*;
import com.coffeeshop.inventory.exception.InventoryNotFoundException;
import com.coffeeshop.inventory.model.InventoryItem;
import com.coffeeshop.inventory.repository.InventoryItemRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.UUID;

@Service
@RequiredArgsConstructor
@Slf4j
public class InventoryService {

    private final InventoryItemRepository repository;

    public InventoryResponse getByProductId(UUID productId) {
        InventoryItem item = repository.findByProductId(productId)
                .orElseThrow(() -> new InventoryNotFoundException(productId));
        return InventoryResponse.from(item);
    }

    @Transactional
    public InventoryResponse add(AddInventoryRequest request) {
        InventoryItem item = repository.findByProductId(request.productId())
                .orElseGet(() -> {
                    InventoryItem newItem = new InventoryItem();
                    newItem.setProductId(request.productId());
                    newItem.setReserved(0);
                    return newItem;
                });
        item.setQuantity(item.getQuantity() + request.quantity());
        InventoryItem saved = repository.save(item);
        log.info("Added {} units for productId={}, total={}", request.quantity(), request.productId(), saved.getQuantity());
        return InventoryResponse.from(saved);
    }

    @Transactional
    public ReservationResponse reserve(UUID productId, ReserveStockRequest request) {
        InventoryItem item = repository.findByProductId(productId)
                .orElseThrow(() -> new InventoryNotFoundException(productId));

        int available = item.availableStock();
        if (available < request.quantity()) {
            log.warn("Insufficient stock for productId={}: requested={}, available={}", productId, request.quantity(), available);
            return new ReservationResponse(false, available, "Insufficient stock");
        }

        item.setReserved(item.getReserved() + request.quantity());
        repository.save(item);
        log.info("Reserved {} units for productId={}, remaining available={}", request.quantity(), productId, item.availableStock());
        return new ReservationResponse(true, item.availableStock(), "Reserved successfully");
    }

    @Transactional
    public InventoryResponse updateQuantity(UUID productId, int quantity) {
        InventoryItem item = repository.findByProductId(productId)
                .orElseThrow(() -> new InventoryNotFoundException(productId));
        item.setQuantity(quantity);
        log.info("Updated quantity for productId={} to {}", productId, quantity);
        return InventoryResponse.from(repository.save(item));
    }
}
