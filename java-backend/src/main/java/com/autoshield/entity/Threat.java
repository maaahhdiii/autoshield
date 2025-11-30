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
import java.util.ArrayList;
import java.util.List;

@Entity
@Table(name = "threats")
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
@EntityListeners(AuditingEntityListener.class)
public class Threat {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false, length = 100)
    private String name;

    @Column(nullable = false, length = 50)
    @Enumerated(EnumType.STRING)
    private ThreatType type;

    @Column(length = 50)
    @Enumerated(EnumType.STRING)
    private ThreatSeverity severity;

    @Column(columnDefinition = "TEXT")
    private String description;

    @Column(name = "source_ip", length = 45)
    private String sourceIp;

    @Column(name = "target_ip", length = 45)
    private String targetIp;

    @Column(name = "target_port")
    private Integer targetPort;

    @Column(length = 50)
    @Enumerated(EnumType.STRING)
    private ThreatStatus status;

    @Column(name = "detection_method", length = 100)
    private String detectionMethod;

    @Column(name = "confidence_score")
    private Double confidenceScore;

    @Column(columnDefinition = "TEXT")
    private String indicators;

    @Column(name = "mitigation_applied")
    private Boolean mitigationApplied = false;

    @Column(name = "mitigation_details", columnDefinition = "TEXT")
    private String mitigationDetails;

    @OneToMany(mappedBy = "threat", cascade = CascadeType.ALL, orphanRemoval = true)
    @Builder.Default
    private List<Alert> alerts = new ArrayList<>();

    @Column(columnDefinition = "jsonb")
    private String metadata;

    @CreatedDate
    @Column(name = "detected_at", nullable = false, updatable = false)
    private LocalDateTime detectedAt;

    @LastModifiedDate
    @Column(name = "updated_at")
    private LocalDateTime updatedAt;

    @Column(name = "mitigated_at")
    private LocalDateTime mitigatedAt;

    public enum ThreatType {
        MALWARE, INTRUSION, DDOS, BRUTE_FORCE, SQL_INJECTION,
        XSS, RANSOMWARE, PHISHING, ANOMALY, VULNERABILITY, OTHER
    }

    public enum ThreatSeverity {
        CRITICAL, HIGH, MEDIUM, LOW
    }

    public enum ThreatStatus {
        ACTIVE, MITIGATED, MONITORING, FALSE_POSITIVE, RESOLVED
    }
}
