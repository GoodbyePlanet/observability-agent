package com.coffeeshop.order.client;

import com.coffeeshop.order.client.dto.ProductResponse;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.http.HttpStatusCode;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClient;

import java.util.UUID;

@Component
@Slf4j
public class CatalogClient {

    private final RestClient restClient;

    public CatalogClient(@Qualifier("catalogRestClient") RestClient restClient) {
        this.restClient = restClient;
    }

    /**
     * Returns the product, or null if not found (404).
     */
    public ProductResponse getProduct(UUID productId) {
        log.info("Calling catalog-service for productId={}", productId);
        return restClient.get()
                .uri("/api/products/{id}", productId)
                .retrieve()
                .onStatus(HttpStatusCode::is4xxClientError, (request, response) -> {
                    log.warn("Product not found in catalog: productId={}", productId);
                    throw new ProductNotFoundInCatalogException(productId);
                })
                .body(ProductResponse.class);
    }

    public static class ProductNotFoundInCatalogException extends RuntimeException {
        public ProductNotFoundInCatalogException(UUID productId) {
            super("Product not found in catalog: " + productId);
        }
    }
}
