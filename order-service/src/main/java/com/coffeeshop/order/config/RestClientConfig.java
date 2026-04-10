package com.coffeeshop.order.config;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.client.RestClient;

@Configuration
public class RestClientConfig {

    @Bean("catalogRestClient")
    public RestClient catalogRestClient(@Value("${coffeeshop.catalog-service.url}") String catalogUrl) {
        return RestClient.builder()
                .baseUrl(catalogUrl)
                .build();
    }

    @Bean("inventoryRestClient")
    public RestClient inventoryRestClient(@Value("${coffeeshop.inventory-service.url}") String inventoryUrl) {
        return RestClient.builder()
                .baseUrl(inventoryUrl)
                .build();
    }
}
