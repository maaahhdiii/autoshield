package com.autoshield.dto;

import com.autoshield.entity.Threat;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ThreatDTO {
    private Long id;
    private String name;
    private Threat.ThreatType type;
    private Threat.ThreatSeverity severity;
    private String description;
    private String sourceIp;
    private String targetIp;
    private Integer targetPort;
    private Threat.ThreatStatus status;
    private String detectionMethod;
    private Double confidenceScore;
    private String indicators;
    private Boolean mitigationApplied;
    private String mitigationDetails;
    private LocalDateTime detectedAt;
    private LocalDateTime updatedAt;
    private LocalDateTime mitigatedAt;
}
