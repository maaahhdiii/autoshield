package com.autoshield.dto;

import com.autoshield.entity.Alert;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class AlertDTO {
    private Long id;
    private Alert.AlertSeverity severity;
    private String title;
    private String description;
    private String sourceModule;
    private String sourceIp;
    private String targetIp;
    private Alert.AlertStatus status;
    private Boolean autoResolved;
    private String resolutionAction;
    private String acknowledgedBy;
    private LocalDateTime acknowledgedAt;
    private Long threatId;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;
}
