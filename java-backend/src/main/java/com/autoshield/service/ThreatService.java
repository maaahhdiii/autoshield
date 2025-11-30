package com.autoshield.service;

import com.autoshield.dto.ThreatDTO;
import com.autoshield.entity.Threat;
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
public class ThreatService {

    private final ThreatRepository threatRepository;

    public ThreatDTO createThreat(ThreatDTO threatDTO) {
        Threat threat = Threat.builder()
                .name(threatDTO.getName())
                .type(threatDTO.getType())
                .severity(threatDTO.getSeverity())
                .description(threatDTO.getDescription())
                .sourceIp(threatDTO.getSourceIp())
                .targetIp(threatDTO.getTargetIp())
                .targetPort(threatDTO.getTargetPort())
                .status(Threat.ThreatStatus.ACTIVE)
                .detectionMethod(threatDTO.getDetectionMethod())
                .confidenceScore(threatDTO.getConfidenceScore())
                .indicators(threatDTO.getIndicators())
                .mitigationApplied(false)
                .build();

        Threat saved = threatRepository.save(threat);
        log.info("Created new threat: {} - {}", saved.getId(), saved.getName());
        return toDTO(saved);
    }

    @Transactional(readOnly = true)
    public List<ThreatDTO> getAllThreats() {
        return threatRepository.findAll().stream()
                .map(this::toDTO)
                .collect(Collectors.toList());
    }

    @Transactional(readOnly = true)
    public Page<ThreatDTO> getThreats(Pageable pageable) {
        return threatRepository.findAll(pageable).map(this::toDTO);
    }

    @Transactional(readOnly = true)
    public ThreatDTO getThreatById(Long id) {
        return threatRepository.findById(id)
                .map(this::toDTO)
                .orElseThrow(() -> new RuntimeException("Threat not found"));
    }

    @Transactional(readOnly = true)
    public List<ThreatDTO> getThreatsByStatus(Threat.ThreatStatus status) {
        return threatRepository.findByStatus(status).stream()
                .map(this::toDTO)
                .collect(Collectors.toList());
    }

    @Transactional(readOnly = true)
    public List<ThreatDTO> getRecentThreats(int limit) {
        return threatRepository.findTop10ByOrderByDetectedAtDesc().stream()
                .limit(limit)
                .map(this::toDTO)
                .collect(Collectors.toList());
    }

    public ThreatDTO updateThreatStatus(Long id, Threat.ThreatStatus status) {
        Threat threat = threatRepository.findById(id)
                .orElseThrow(() -> new RuntimeException("Threat not found"));
        
        threat.setStatus(status);
        
        if (status == Threat.ThreatStatus.MITIGATED || status == Threat.ThreatStatus.RESOLVED) {
            threat.setMitigatedAt(LocalDateTime.now());
        }
        
        Threat updated = threatRepository.save(threat);
        log.info("Updated threat {} status to {}", id, status);
        return toDTO(updated);
    }

    public ThreatDTO applyMitigation(Long id, String mitigationDetails) {
        Threat threat = threatRepository.findById(id)
                .orElseThrow(() -> new RuntimeException("Threat not found"));
        
        threat.setMitigationApplied(true);
        threat.setMitigationDetails(mitigationDetails);
        threat.setStatus(Threat.ThreatStatus.MITIGATED);
        threat.setMitigatedAt(LocalDateTime.now());
        
        Threat updated = threatRepository.save(threat);
        log.info("Applied mitigation to threat {}", id);
        return toDTO(updated);
    }

    public void deleteThreat(Long id) {
        threatRepository.deleteById(id);
        log.info("Deleted threat {}", id);
    }

    @Transactional(readOnly = true)
    public Long countActiveThreats() {
        return threatRepository.countByStatus(Threat.ThreatStatus.ACTIVE);
    }

    @Transactional(readOnly = true)
    public Long countMitigatedThreats() {
        return threatRepository.countByStatusAndMitigationApplied(Threat.ThreatStatus.MITIGATED);
    }

    private ThreatDTO toDTO(Threat threat) {
        return ThreatDTO.builder()
                .id(threat.getId())
                .name(threat.getName())
                .type(threat.getType())
                .severity(threat.getSeverity())
                .description(threat.getDescription())
                .sourceIp(threat.getSourceIp())
                .targetIp(threat.getTargetIp())
                .targetPort(threat.getTargetPort())
                .status(threat.getStatus())
                .detectionMethod(threat.getDetectionMethod())
                .confidenceScore(threat.getConfidenceScore())
                .indicators(threat.getIndicators())
                .mitigationApplied(threat.getMitigationApplied())
                .mitigationDetails(threat.getMitigationDetails())
                .detectedAt(threat.getDetectedAt())
                .updatedAt(threat.getUpdatedAt())
                .mitigatedAt(threat.getMitigatedAt())
                .build();
    }
}
