package com.autoshield.repository;

import com.autoshield.entity.Threat;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.time.LocalDateTime;
import java.util.List;

@Repository
public interface ThreatRepository extends JpaRepository<Threat, Long> {

    List<Threat> findByStatus(Threat.ThreatStatus status);

    List<Threat> findBySeverity(Threat.ThreatSeverity severity);

    Page<Threat> findByStatus(Threat.ThreatStatus status, Pageable pageable);

    @Query("SELECT COUNT(t) FROM Threat t WHERE t.status = :status")
    Long countByStatus(@Param("status") Threat.ThreatStatus status);

    @Query("SELECT COUNT(t) FROM Threat t WHERE t.status = :status AND t.mitigationApplied = true")
    Long countByStatusAndMitigationApplied(@Param("status") Threat.ThreatStatus status);

    List<Threat> findByDetectedAtBetween(LocalDateTime start, LocalDateTime end);

    List<Threat> findTop10ByOrderByDetectedAtDesc();

    @Query("SELECT t FROM Threat t WHERE t.sourceIp = :ip OR t.targetIp = :ip")
    List<Threat> findByIpAddress(@Param("ip") String ip);

    List<Threat> findByType(Threat.ThreatType type);
}
