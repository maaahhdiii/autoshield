package com.autoshield.entity;

import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;
import org.springframework.data.annotation.CreatedDate;
import org.springframework.data.annotation.LastModifiedDate;
import org.springframework.data.jpa.domain.support.AuditingEntityListener;

import java.time.LocalDateTime;

@Entity
@Table(name = "scans")
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
@EntityListeners(AuditingEntityListener.class)
public class Scan {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false, length = 50)
    @Enumerated(EnumType.STRING)
    private ScanType type;

    @Column(nullable = false, length = 100)
    private String target;

    @Column(length = 50)
    @Enumerated(EnumType.STRING)
    private ScanStatus status;

    @Column(name = "started_by", length = 100)
    private String startedBy;

    @Column(name = "scan_profile", length = 100)
    private String scanProfile;

    @Column(name = "findings_count")
    private Integer findingsCount = 0;

    @Column(name = "vulnerabilities_found")
    private Integer vulnerabilitiesFound = 0;

    @Column(name = "threats_detected")
    private Integer threatsDetected = 0;

    @Column(columnDefinition = "TEXT")
    private String results;

    @Column(name = "error_message", length = 500)
    private String errorMessage;

    @Column(name = "duration_seconds")
    private Long durationSeconds;

    @Column(columnDefinition = "jsonb")
    private String parameters;

    @CreatedDate
    @Column(name = "started_at", nullable = false, updatable = false)
    private LocalDateTime startedAt;

    @Column(name = "completed_at")
    private LocalDateTime completedAt;

    @LastModifiedDate
    @Column(name = "updated_at")
    private LocalDateTime updatedAt;

    public enum ScanType {
        NETWORK, PORT, VULNERABILITY, MALWARE, FULL
    }

    public enum ScanStatus {
        PENDING, RUNNING, COMPLETED, FAILED, CANCELLED
    }
}
