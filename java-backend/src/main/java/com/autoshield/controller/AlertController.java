package com.autoshield.controller;

import com.autoshield.dto.AlertDTO;
import com.autoshield.entity.Alert;
import com.autoshield.service.AlertService;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/alerts")
@RequiredArgsConstructor
@CrossOrigin(origins = "*")
public class AlertController {

    private final AlertService alertService;

    @PostMapping
    public ResponseEntity<AlertDTO> createAlert(@Valid @RequestBody AlertDTO alertDTO) {
        AlertDTO created = alertService.createAlert(alertDTO);
        return ResponseEntity.status(HttpStatus.CREATED).body(created);
    }

    @GetMapping
    public ResponseEntity<List<AlertDTO>> getAllAlerts() {
        return ResponseEntity.ok(alertService.getAllAlerts());
    }

    @GetMapping("/paged")
    public ResponseEntity<Page<AlertDTO>> getAlertsPaged(Pageable pageable) {
        return ResponseEntity.ok(alertService.getAlerts(pageable));
    }

    @GetMapping("/{id}")
    public ResponseEntity<AlertDTO> getAlertById(@PathVariable Long id) {
        return ResponseEntity.ok(alertService.getAlertById(id));
    }

    @GetMapping("/status/{status}")
    public ResponseEntity<List<AlertDTO>> getAlertsByStatus(@PathVariable Alert.AlertStatus status) {
        return ResponseEntity.ok(alertService.getAlertsByStatus(status));
    }

    @GetMapping("/severity/{severity}")
    public ResponseEntity<List<AlertDTO>> getAlertsBySeverity(@PathVariable Alert.AlertSeverity severity) {
        return ResponseEntity.ok(alertService.getAlertsBySeverity(severity));
    }

    @GetMapping("/recent")
    public ResponseEntity<List<AlertDTO>> getRecentAlerts(@RequestParam(defaultValue = "10") int limit) {
        return ResponseEntity.ok(alertService.getRecentAlerts(limit));
    }

    @PutMapping("/{id}/status")
    public ResponseEntity<AlertDTO> updateAlertStatus(
            @PathVariable Long id,
            @RequestParam Alert.AlertStatus status) {
        return ResponseEntity.ok(alertService.updateAlertStatus(id, status));
    }

    @PutMapping("/{id}/acknowledge")
    public ResponseEntity<AlertDTO> acknowledgeAlert(
            @PathVariable Long id,
            @RequestParam String acknowledgedBy) {
        return ResponseEntity.ok(alertService.acknowledgeAlert(id, acknowledgedBy));
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<Void> deleteAlert(@PathVariable Long id) {
        alertService.deleteAlert(id);
        return ResponseEntity.noContent().build();
    }

    @GetMapping("/count/status/{status}")
    public ResponseEntity<Long> countAlertsByStatus(@PathVariable Alert.AlertStatus status) {
        return ResponseEntity.ok(alertService.countAlertsByStatus(status));
    }

    @GetMapping("/count/critical")
    public ResponseEntity<Long> countCriticalAlerts() {
        return ResponseEntity.ok(alertService.countCriticalAlerts());
    }
}
