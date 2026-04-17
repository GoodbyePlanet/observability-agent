package com.coffeeshop.catalog.service;

import com.coffeeshop.catalog.dto.ProductRequest;
import com.coffeeshop.catalog.dto.ProductResponse;
import com.coffeeshop.catalog.exception.ProductNotFoundException;
import com.coffeeshop.catalog.model.Product;
import com.coffeeshop.catalog.repository.ProductRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.UUID;

@Service
@RequiredArgsConstructor
@Slf4j
public class ProductService {

    private final ProductRepository productRepository;

    public List<ProductResponse> findAll() {
        log.info("Fetching all products");
        try {
            Thread.sleep(2000);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            log.error("Thread interrupted while fetching products", e);
        }
        return productRepository.findAll().stream()
                .map(ProductResponse::from)
                .toList();
    }

    public ProductResponse findById(UUID id) {
        log.info("Fetching product id={}", id);
        return productRepository.findById(id)
                .map(ProductResponse::from)
                .orElseThrow(() -> {
                    log.error("Product lookup failed - no product with id={}", id);
                    return new ProductNotFoundException(id);
                });
    }

    @Transactional
    public ProductResponse create(ProductRequest request) {
        Product product = new Product();
        product.setName(request.name());
        product.setDescription(request.description());
        product.setPrice(request.price());
        product.setCategory(request.category());
        Product saved = productRepository.save(product);
        log.info("Created product id={} name={}", saved.getId(), saved.getName());
        return ProductResponse.from(saved);
    }

    @Transactional
    public ProductResponse update(UUID id, ProductRequest request) {
        Product product = productRepository.findById(id)
                .orElseThrow(() -> {
                    log.error("Cannot update product - not found: id={}", id);
                    return new ProductNotFoundException(id);
                });
        product.setName(request.name());
        product.setDescription(request.description());
        product.setPrice(request.price());
        product.setCategory(request.category());
        log.info("Updated product id={}", id);
        return ProductResponse.from(productRepository.save(product));
    }

    @Transactional
    public void delete(UUID id) {
        if (!productRepository.existsById(id)) {
            log.error("Cannot delete product - not found: id={}", id);
            throw new ProductNotFoundException(id);
        }
        productRepository.deleteById(id);
        log.info("Deleted product id={}", id);
    }
}
