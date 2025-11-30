package com.autoshield.repository;

import com.autoshield.entity.Scan;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.time.LocalDateTime;
import java.util.List;

@Repository
public interface ScanRepository extends JpaRepository<Scan, Long> {

    List<Scan> findByStatus(Scan.ScanStatus status);

    Page<Scan> findByStatus(Scan.ScanStatus status, Pageable pageable);

    @Query("SELECT COUNT(s) FROM Scan s WHERE s.status = :status")
    Long countByStatus(@Param("status") Scan.ScanStatus status);

    List<Scan> findByStartedAtBetween(LocalDateTime start, LocalDateTime end);

    List<Scan> findTop10ByOrderByStartedAtDesc();

    List<Scan> findByType(Scan.ScanType type);

    @Query("SELECT s FROM Scan s WHERE s.status IN :statuses ORDER BY s.startedAt DESC")
    List<Scan> findByStatusIn(@Param("statuses") List<Scan.ScanStatus> statuses);
}
