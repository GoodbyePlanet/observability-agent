package com.coffeeshop.catalog.repository;

import com.coffeeshop.catalog.model.Product;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.UUID;

public interface ProductRepository extends JpaRepository<Product, UUID> {}
