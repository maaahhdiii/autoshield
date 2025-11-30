package com.autoshield.service;

import com.autoshield.dto.DashboardDTO;
import com.autoshield.entity.Alert;
import com.autoshield.entity.Scan;
import com.autoshield.entity.Threat;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.stereotype.Service;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.core.publisher.Mono;

import java.time.Duration;
import java.util.List;

@Service
@RequiredArgsConstructor
@Slf4j
public class DashboardService {

    private final AlertService alertService;
    private final ThreatService threatService;
    private final ScanService scanService;

    @Qualifier("pythonAiWebClient")
    private final WebClient pythonAiWebClient;

    @Qualifier("kaliMcpWebClient")
    private final WebClient kaliMcpWebClient;

    public DashboardDTO getDashboardData() {
        // Get statistics
        Long totalAlerts = alertService.countAlertsByStatus(Alert.AlertStatus.NEW) +
                          alertService.countAlertsByStatus(Alert.AlertStatus.ACKNOWLEDGED) +
                          alertService.countAlertsByStatus(Alert.AlertStatus.IN_PROGRESS);
        
        Long criticalAlerts = alertService.countCriticalAlerts();
        Long activeThreats = threatService.countActiveThreats();
        Long completedScans = scanService.countScansByStatus(Scan.ScanStatus.COMPLETED);
        Long runningScans = scanService.countScansByStatus(Scan.ScanStatus.RUNNING);
        
        Long totalThreats = activeThreats + 
                           threatService.getThreatsByStatus(Threat.ThreatStatus.MITIGATED).size() +
                           threatService.getThreatsByStatus(Threat.ThreatStatus.RESOLVED).size();
        
        Long mitigatedThreats = threatService.countMitigatedThreats();

        DashboardDTO.Statistics statistics = DashboardDTO.Statistics.builder()
                .totalAlerts(totalAlerts)
                .criticalAlerts(criticalAlerts)
                .activeThreats(activeThreats)
                .completedScans(completedScans)
                .runningScans(runningScans)
                .totalThreats(totalThreats)
                .mitigatedThreats(mitigatedThreats)
                .build();

        // Get system health
        String pythonAiStatus = checkServiceHealth(pythonAiWebClient, "Python AI");
        String kaliMcpStatus = checkServiceHealth(kaliMcpWebClient, "Kali MCP");
        String databaseStatus = "UP"; // Assume DB is up if this code is running
        
        String overallStatus = determineOverallStatus(pythonAiStatus, kaliMcpStatus, databaseStatus);

        DashboardDTO.SystemHealth systemHealth = DashboardDTO.SystemHealth.builder()
                .pythonAiStatus(pythonAiStatus)
                .kaliMcpStatus(kaliMcpStatus)
                .databaseStatus(databaseStatus)
                .overallStatus(overallStatus)
                .build();

        return DashboardDTO.builder()
                .statistics(statistics)
                .systemHealth(systemHealth)
                .build();
    }

    private String checkServiceHealth(WebClient webClient, String serviceName) {
        try {
            String status = webClient.get()
                    .uri("/health")
                    .retrieve()
                    .bodyToMono(String.class)
                    .timeout(Duration.ofSeconds(5))
                    .onErrorResume(e -> Mono.just("DOWN"))
                    .block();
            
            log.debug("{} health check: {}", serviceName, status);
            return status != null && status.contains("UP") ? "UP" : "DOWN";
        } catch (Exception e) {
            log.warn("{} health check failed: {}", serviceName, e.getMessage());
            return "DOWN";
        }
    }

    private String determineOverallStatus(String... statuses) {
        for (String status : statuses) {
            if ("DOWN".equals(status)) {
                return "DEGRADED";
            }
        }
        return "UP";
    }
}
