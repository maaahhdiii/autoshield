package com.autoshield.controller;

import com.autoshield.dto.ThreatDTO;
import com.autoshield.entity.Threat;
import com.autoshield.service.ThreatService;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/threats")
@RequiredArgsConstructor
@CrossOrigin(origins = "*")
public class ThreatController {

    private final ThreatService threatService;

    @PostMapping
    public ResponseEntity<ThreatDTO> createThreat(@Valid @RequestBody ThreatDTO threatDTO) {
        ThreatDTO created = threatService.createThreat(threatDTO);
        return ResponseEntity.status(HttpStatus.CREATED).body(created);
    }

    @GetMapping
    public ResponseEntity<List<ThreatDTO>> getAllThreats() {
        return ResponseEntity.ok(threatService.getAllThreats());
    }

    @GetMapping("/paged")
    public ResponseEntity<Page<ThreatDTO>> getThreatsPaged(Pageable pageable) {
        return ResponseEntity.ok(threatService.getThreats(pageable));
    }

    @GetMapping("/{id}")
    public ResponseEntity<ThreatDTO> getThreatById(@PathVariable Long id) {
        return ResponseEntity.ok(threatService.getThreatById(id));
    }

    @GetMapping("/status/{status}")
    public ResponseEntity<List<ThreatDTO>> getThreatsByStatus(@PathVariable Threat.ThreatStatus status) {
        return ResponseEntity.ok(threatService.getThreatsByStatus(status));
    }

    @GetMapping("/recent")
    public ResponseEntity<List<ThreatDTO>> getRecentThreats(@RequestParam(defaultValue = "10") int limit) {
        return ResponseEntity.ok(threatService.getRecentThreats(limit));
    }

    @PutMapping("/{id}/status")
    public ResponseEntity<ThreatDTO> updateThreatStatus(
            @PathVariable Long id,
            @RequestParam Threat.ThreatStatus status) {
        return ResponseEntity.ok(threatService.updateThreatStatus(id, status));
    }

    @PutMapping("/{id}/mitigate")
    public ResponseEntity<ThreatDTO> applyMitigation(
            @PathVariable Long id,
            @RequestBody Map<String, String> request) {
        String mitigationDetails = request.get("mitigationDetails");
        return ResponseEntity.ok(threatService.applyMitigation(id, mitigationDetails));
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<Void> deleteThreat(@PathVariable Long id) {
        threatService.deleteThreat(id);
        return ResponseEntity.noContent().build();
    }

    @GetMapping("/count/active")
    public ResponseEntity<Long> countActiveThreats() {
        return ResponseEntity.ok(threatService.countActiveThreats());
    }

    @GetMapping("/count/mitigated")
    public ResponseEntity<Long> countMitigatedThreats() {
        return ResponseEntity.ok(threatService.countMitigatedThreats());
    }
}
