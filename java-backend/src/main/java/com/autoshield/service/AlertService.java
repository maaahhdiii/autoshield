package com.autoshield.service;

import com.autoshield.dto.AlertDTO;
import com.autoshield.entity.Alert;
import com.autoshield.entity.Threat;
import com.autoshield.repository.AlertRepository;
import com.autoshield.repository.ThreatRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.List;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
@Slf4j
@Transactional
public class AlertService {

    private final AlertRepository alertRepository;
    private final ThreatRepository threatRepository;

    public AlertDTO createAlert(AlertDTO alertDTO) {
        Alert alert = Alert.builder()
                .severity(alertDTO.getSeverity())
                .title(alertDTO.getTitle())
                .description(alertDTO.getDescription())
                .sourceModule(alertDTO.getSourceModule())
                .sourceIp(alertDTO.getSourceIp())
                .targetIp(alertDTO.getTargetIp())
                .status(Alert.AlertStatus.NEW)
                .autoResolved(false)
                .build();

        if (alertDTO.getThreatId() != null) {
            Threat threat = threatRepository.findById(alertDTO.getThreatId())
                    .orElseThrow(() -> new RuntimeException("Threat not found"));
            alert.setThreat(threat);
        }

        Alert saved = alertRepository.save(alert);
        log.info("Created new alert: {} - {}", saved.getId(), saved.getTitle());
        return toDTO(saved);
    }

    @Transactional(readOnly = true)
    public List<AlertDTO> getAllAlerts() {
        return alertRepository.findAll().stream()
                .map(this::toDTO)
                .collect(Collectors.toList());
    }

    @Transactional(readOnly = true)
    public Page<AlertDTO> getAlerts(Pageable pageable) {
        return alertRepository.findAll(pageable).map(this::toDTO);
    }

    @Transactional(readOnly = true)
    public AlertDTO getAlertById(Long id) {
        return alertRepository.findById(id)
                .map(this::toDTO)
                .orElseThrow(() -> new RuntimeException("Alert not found"));
    }

    @Transactional(readOnly = true)
    public List<AlertDTO> getAlertsByStatus(Alert.AlertStatus status) {
        return alertRepository.findByStatus(status).stream()
                .map(this::toDTO)
                .collect(Collectors.toList());
    }

    @Transactional(readOnly = true)
    public List<AlertDTO> getAlertsBySeverity(Alert.AlertSeverity severity) {
        return alertRepository.findBySeverity(severity).stream()
                .map(this::toDTO)
                .collect(Collectors.toList());
    }

    @Transactional(readOnly = true)
    public List<AlertDTO> getRecentAlerts(int limit) {
        return alertRepository.findTop10ByOrderByCreatedAtDesc().stream()
                .limit(limit)
                .map(this::toDTO)
                .collect(Collectors.toList());
    }

    public AlertDTO updateAlertStatus(Long id, Alert.AlertStatus status) {
        Alert alert = alertRepository.findById(id)
                .orElseThrow(() -> new RuntimeException("Alert not found"));
        
        alert.setStatus(status);
        
        if (status == Alert.AlertStatus.RESOLVED) {
            alert.setAutoResolved(false);
        }
        
        Alert updated = alertRepository.save(alert);
        log.info("Updated alert {} status to {}", id, status);
        return toDTO(updated);
    }

    public AlertDTO acknowledgeAlert(Long id, String acknowledgedBy) {
        Alert alert = alertRepository.findById(id)
                .orElseThrow(() -> new RuntimeException("Alert not found"));
        
        alert.setStatus(Alert.AlertStatus.ACKNOWLEDGED);
        alert.setAcknowledgedBy(acknowledgedBy);
        alert.setAcknowledgedAt(LocalDateTime.now());
        
        Alert updated = alertRepository.save(alert);
        log.info("Alert {} acknowledged by {}", id, acknowledgedBy);
        return toDTO(updated);
    }

    public void deleteAlert(Long id) {
        alertRepository.deleteById(id);
        log.info("Deleted alert {}", id);
    }

    @Transactional(readOnly = true)
    public Long countAlertsByStatus(Alert.AlertStatus status) {
        return alertRepository.countByStatus(status);
    }

    @Transactional(readOnly = true)
    public Long countCriticalAlerts() {
        return alertRepository.countBySeverityAndStatusIn(
                Alert.AlertSeverity.CRITICAL,
                List.of(Alert.AlertStatus.NEW, Alert.AlertStatus.ACKNOWLEDGED, Alert.AlertStatus.IN_PROGRESS)
        );
    }

    private AlertDTO toDTO(Alert alert) {
        return AlertDTO.builder()
                .id(alert.getId())
                .severity(alert.getSeverity())
                .title(alert.getTitle())
                .description(alert.getDescription())
                .sourceModule(alert.getSourceModule())
                .sourceIp(alert.getSourceIp())
                .targetIp(alert.getTargetIp())
                .status(alert.getStatus())
                .autoResolved(alert.getAutoResolved())
                .resolutionAction(alert.getResolutionAction())
                .acknowledgedBy(alert.getAcknowledgedBy())
                .acknowledgedAt(alert.getAcknowledgedAt())
                .threatId(alert.getThreat() != null ? alert.getThreat().getId() : null)
                .createdAt(alert.getCreatedAt())
                .updatedAt(alert.getUpdatedAt())
                .build();
    }
}
