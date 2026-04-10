package com.coffeeshop.order.client;

import com.coffeeshop.order.client.dto.ReservationResponse;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClient;

import java.util.Map;
import java.util.UUID;

@Component
@Slf4j
public class InventoryClient {

    private final RestClient restClient;

    public InventoryClient(@Qualifier("inventoryRestClient") RestClient restClient) {
        this.restClient = restClient;
    }

    public ReservationResponse reserve(UUID productId, int quantity) {
        log.info("Calling inventory-service to reserve {} units for productId={}", quantity, productId);
        return restClient.post()
                .uri("/api/inventory/{productId}/reserve", productId)
                .body(Map.of("quantity", quantity))
                .retrieve()
                .body(ReservationResponse.class);
    }
}
