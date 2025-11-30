package com.autoshield.repository;

import com.autoshield.entity.Configuration;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

@Repository
public interface ConfigurationRepository extends JpaRepository<Configuration, Long> {

    Optional<Configuration> findByKey(String key);

    List<Configuration> findByCategory(String category);

    boolean existsByKey(String key);
}
