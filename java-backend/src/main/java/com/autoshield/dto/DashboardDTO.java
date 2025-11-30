package com.autoshield.dto;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class DashboardDTO {
    private Statistics statistics;
    private SystemHealth systemHealth;

    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    public static class Statistics {
        private Long totalAlerts;
        private Long criticalAlerts;
        private Long activeThreats;
        private Long completedScans;
        private Long runningScans;
        private Long totalThreats;
        private Long mitigatedThreats;
    }

    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    public static class SystemHealth {
        private String pythonAiStatus;
        private String kaliMcpStatus;
        private String databaseStatus;
        private String overallStatus;
    }
}
