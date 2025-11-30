package com.autoshield.repository;

import com.autoshield.entity.Alert;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.time.LocalDateTime;
import java.util.List;

@Repository
public interface AlertRepository extends JpaRepository<Alert, Long> {

    List<Alert> findByStatus(Alert.AlertStatus status);

    List<Alert> findBySeverity(Alert.AlertSeverity severity);

    Page<Alert> findByStatus(Alert.AlertStatus status, Pageable pageable);

    Page<Alert> findBySeverity(Alert.AlertSeverity severity, Pageable pageable);

    @Query("SELECT a FROM Alert a WHERE a.status IN :statuses ORDER BY a.createdAt DESC")
    List<Alert> findByStatusIn(@Param("statuses") List<Alert.AlertStatus> statuses);

    @Query("SELECT COUNT(a) FROM Alert a WHERE a.status = :status")
    Long countByStatus(@Param("status") Alert.AlertStatus status);

    @Query("SELECT COUNT(a) FROM Alert a WHERE a.severity = :severity AND a.status IN :statuses")
    Long countBySeverityAndStatusIn(@Param("severity") Alert.AlertSeverity severity, 
                                     @Param("statuses") List<Alert.AlertStatus> statuses);

    List<Alert> findByCreatedAtBetween(LocalDateTime start, LocalDateTime end);

    List<Alert> findTop10ByOrderByCreatedAtDesc();

    @Query("SELECT a FROM Alert a WHERE a.threat.id = :threatId")
    List<Alert> findByThreatId(@Param("threatId") Long threatId);
}
