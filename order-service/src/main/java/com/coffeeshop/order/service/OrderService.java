package com.coffeeshop.order.service;

import com.coffeeshop.order.client.CatalogClient;
import com.coffeeshop.order.client.CatalogClient.ProductNotFoundInCatalogException;
import com.coffeeshop.order.client.InventoryClient;
import com.coffeeshop.order.client.dto.ProductResponse;
import com.coffeeshop.order.client.dto.ReservationResponse;
import com.coffeeshop.order.dto.OrderResponse;
import com.coffeeshop.order.dto.PlaceOrderRequest;
import com.coffeeshop.order.exception.OrderNotFoundException;
import com.coffeeshop.order.model.Order;
import com.coffeeshop.order.model.OrderStatus;
import com.coffeeshop.order.repository.OrderRepository;
import io.opentelemetry.api.trace.Span;
import io.opentelemetry.instrumentation.annotations.WithSpan;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.util.List;
import java.util.UUID;

@Service
@RequiredArgsConstructor
@Slf4j
public class OrderService {

    private final OrderRepository orderRepository;
    private final CatalogClient catalogClient;
    private final InventoryClient inventoryClient;

    public List<OrderResponse> findAll() {
        return orderRepository.findAll().stream()
                .map(OrderResponse::from)
                .toList();
    }

    public OrderResponse findById(UUID id) {
        return orderRepository.findById(id)
                .map(OrderResponse::from)
                .orElseThrow(() -> new OrderNotFoundException(id));
    }

    @WithSpan("order.place")
    @Transactional
    public OrderResponse placeOrder(PlaceOrderRequest request) {
        Span.current().setAttribute("order.product_id", request.productId().toString());
        Span.current().setAttribute("order.quantity", request.quantity());
        log.info("Placing order: productId={}, quantity={}", request.productId(), request.quantity());

        Order order = new Order();
        order.setProductId(request.productId());
        order.setQuantity(request.quantity());
        order.setStatus(OrderStatus.PENDING);

        // Step 1: Get product details from catalog-service
        ProductResponse product;
        try {
            product = catalogClient.getProduct(request.productId());
        } catch (ProductNotFoundInCatalogException ex) {
            log.warn("Order failed - product not found: {}", request.productId());
            order.setProductName("Unknown");
            order.setUnitPrice(BigDecimal.ZERO);
            order.setTotalPrice(BigDecimal.ZERO);
            order.setStatus(OrderStatus.FAILED);
            order.setFailureReason("Product not found in catalog");
            return OrderResponse.from(orderRepository.save(order));
        }

        order.setProductName(product.name());
        order.setUnitPrice(product.price());
        order.setTotalPrice(product.price().multiply(BigDecimal.valueOf(request.quantity())));

        // Step 2: Reserve stock in inventory-service
        ReservationResponse reservation = inventoryClient.reserve(request.productId(), request.quantity());

        if (!reservation.success()) {
            log.warn("Order failed - insufficient stock: productId={}, requested={}, available={}",
                    request.productId(), request.quantity(), reservation.availableStock());
            order.setStatus(OrderStatus.FAILED);
            order.setFailureReason("Insufficient stock: " + reservation.message());
            return OrderResponse.from(orderRepository.save(order));
        }

        order.setStatus(OrderStatus.CONFIRMED);
        Order saved = orderRepository.save(order);
        log.info("Order confirmed: id={}, product={}, total={}", saved.getId(), product.name(), saved.getTotalPrice());
        return OrderResponse.from(saved);
    }
}
