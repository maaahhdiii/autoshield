package com.autoshield.service;

import com.autoshield.dto.ScanDTO;
import com.autoshield.dto.ScanRequestDTO;
import com.autoshield.entity.Scan;
import com.autoshield.repository.ScanRepository;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.reactive.function.client.WebClient;

import java.time.Duration;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
@Slf4j
@Transactional
public class ScanService {

    private final ScanRepository scanRepository;
    
    @Qualifier("kaliMcpWebClient")
    private final WebClient kaliMcpWebClient;
    
    private final ObjectMapper objectMapper;

    public ScanDTO initiateScan(ScanRequestDTO request, String startedBy) {
        Scan scan = Scan.builder()
                .type(request.getType())
                .target(request.getTarget())
                .status(Scan.ScanStatus.PENDING)
                .startedBy(startedBy)
                .scanProfile(request.getScanProfile())
                .findingsCount(0)
                .vulnerabilitiesFound(0)
                .threatsDetected(0)
                .build();

        if (request.getParameters() != null) {
            try {
                scan.setParameters(objectMapper.writeValueAsString(request.getParameters()));
            } catch (Exception e) {
                log.error("Failed to serialize scan parameters", e);
            }
        }

        Scan saved = scanRepository.save(scan);
        log.info("Initiated scan: {} - {} on {}", saved.getId(), saved.getType(), saved.getTarget());

        // Start scan asynchronously
        executeScanAsync(saved.getId());

        return toDTO(saved);
    }

    private void executeScanAsync(Long scanId) {
        // This would be executed in a separate thread or using @Async
        // For now, just update status to RUNNING
        scanRepository.findById(scanId).ifPresent(scan -> {
            scan.setStatus(Scan.ScanStatus.RUNNING);
            scanRepository.save(scan);
            log.info("Scan {} is now running", scanId);
        });
    }

    public ScanDTO updateScanResults(Long id, Map<String, Object> results) {
        Scan scan = scanRepository.findById(id)
                .orElseThrow(() -> new RuntimeException("Scan not found"));

        try {
            scan.setResults(objectMapper.writeValueAsString(results));
            scan.setStatus(Scan.ScanStatus.COMPLETED);
            scan.setCompletedAt(LocalDateTime.now());
            
            Duration duration = Duration.between(scan.getStartedAt(), scan.getCompletedAt());
            scan.setDurationSeconds(duration.getSeconds());

            // Extract counts from results
            if (results.containsKey("findings_count")) {
                scan.setFindingsCount(((Number) results.get("findings_count")).intValue());
            }
            if (results.containsKey("vulnerabilities")) {
                scan.setVulnerabilitiesFound(((Number) results.get("vulnerabilities")).intValue());
            }
            if (results.containsKey("threats")) {
                scan.setThreatsDetected(((Number) results.get("threats")).intValue());
            }

            Scan updated = scanRepository.save(scan);
            log.info("Updated scan {} with results", id);
            return toDTO(updated);
        } catch (Exception e) {
            log.error("Failed to update scan results", e);
            throw new RuntimeException("Failed to update scan results", e);
        }
    }

    @Transactional(readOnly = true)
    public List<ScanDTO> getAllScans() {
        return scanRepository.findAll().stream()
                .map(this::toDTO)
                .collect(Collectors.toList());
    }

    @Transactional(readOnly = true)
    public Page<ScanDTO> getScans(Pageable pageable) {
        return scanRepository.findAll(pageable).map(this::toDTO);
    }

    @Transactional(readOnly = true)
    public ScanDTO getScanById(Long id) {
        return scanRepository.findById(id)
                .map(this::toDTO)
                .orElseThrow(() -> new RuntimeException("Scan not found"));
    }

    @Transactional(readOnly = true)
    public List<ScanDTO> getScansByStatus(Scan.ScanStatus status) {
        return scanRepository.findByStatus(status).stream()
                .map(this::toDTO)
                .collect(Collectors.toList());
    }

    @Transactional(readOnly = true)
    public List<ScanDTO> getRecentScans(int limit) {
        return scanRepository.findTop10ByOrderByStartedAtDesc().stream()
                .limit(limit)
                .map(this::toDTO)
                .collect(Collectors.toList());
    }

    public ScanDTO cancelScan(Long id) {
        Scan scan = scanRepository.findById(id)
                .orElseThrow(() -> new RuntimeException("Scan not found"));
        
        if (scan.getStatus() == Scan.ScanStatus.RUNNING || scan.getStatus() == Scan.ScanStatus.PENDING) {
            scan.setStatus(Scan.ScanStatus.CANCELLED);
            scan.setCompletedAt(LocalDateTime.now());
            Scan updated = scanRepository.save(scan);
            log.info("Cancelled scan {}", id);
            return toDTO(updated);
        }
        
        throw new RuntimeException("Cannot cancel scan in status: " + scan.getStatus());
    }

    public void deleteScan(Long id) {
        scanRepository.deleteById(id);
        log.info("Deleted scan {}", id);
    }

    @Transactional(readOnly = true)
    public Long countScansByStatus(Scan.ScanStatus status) {
        return scanRepository.countByStatus(status);
    }

    private ScanDTO toDTO(Scan scan) {
        return ScanDTO.builder()
                .id(scan.getId())
                .type(scan.getType())
                .target(scan.getTarget())
                .status(scan.getStatus())
                .startedBy(scan.getStartedBy())
                .scanProfile(scan.getScanProfile())
                .findingsCount(scan.getFindingsCount())
                .vulnerabilitiesFound(scan.getVulnerabilitiesFound())
                .threatsDetected(scan.getThreatsDetected())
                .results(scan.getResults())
                .errorMessage(scan.getErrorMessage())
                .durationSeconds(scan.getDurationSeconds())
                .startedAt(scan.getStartedAt())
                .completedAt(scan.getCompletedAt())
                .updatedAt(scan.getUpdatedAt())
                .build();
    }
}
