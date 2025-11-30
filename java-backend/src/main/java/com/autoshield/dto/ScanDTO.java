package com.autoshield.dto;

import com.autoshield.entity.Scan;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ScanDTO {
    private Long id;
    private Scan.ScanType type;
    private String target;
    private Scan.ScanStatus status;
    private String startedBy;
    private String scanProfile;
    private Integer findingsCount;
    private Integer vulnerabilitiesFound;
    private Integer threatsDetected;
    private String results;
    private String errorMessage;
    private Long durationSeconds;
    private LocalDateTime startedAt;
    private LocalDateTime completedAt;
    private LocalDateTime updatedAt;
}
