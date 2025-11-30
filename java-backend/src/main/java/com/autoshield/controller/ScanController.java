package com.autoshield.controller;

import com.autoshield.dto.ScanDTO;
import com.autoshield.dto.ScanRequestDTO;
import com.autoshield.entity.Scan;
import com.autoshield.service.ScanService;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/scans")
@RequiredArgsConstructor
@CrossOrigin(origins = "*")
public class ScanController {

    private final ScanService scanService;

    @PostMapping
    public ResponseEntity<ScanDTO> initiateScan(
            @Valid @RequestBody ScanRequestDTO request,
            Authentication authentication) {
        String startedBy = authentication != null ? authentication.getName() : "system";
        ScanDTO created = scanService.initiateScan(request, startedBy);
        return ResponseEntity.status(HttpStatus.CREATED).body(created);
    }

    @GetMapping
    public ResponseEntity<List<ScanDTO>> getAllScans() {
        return ResponseEntity.ok(scanService.getAllScans());
    }

    @GetMapping("/paged")
    public ResponseEntity<Page<ScanDTO>> getScansPaged(Pageable pageable) {
        return ResponseEntity.ok(scanService.getScans(pageable));
    }

    @GetMapping("/{id}")
    public ResponseEntity<ScanDTO> getScanById(@PathVariable Long id) {
        return ResponseEntity.ok(scanService.getScanById(id));
    }

    @GetMapping("/status/{status}")
    public ResponseEntity<List<ScanDTO>> getScansByStatus(@PathVariable Scan.ScanStatus status) {
        return ResponseEntity.ok(scanService.getScansByStatus(status));
    }

    @GetMapping("/recent")
    public ResponseEntity<List<ScanDTO>> getRecentScans(@RequestParam(defaultValue = "10") int limit) {
        return ResponseEntity.ok(scanService.getRecentScans(limit));
    }

    @PutMapping("/{id}/results")
    public ResponseEntity<ScanDTO> updateScanResults(
            @PathVariable Long id,
            @RequestBody Map<String, Object> results) {
        return ResponseEntity.ok(scanService.updateScanResults(id, results));
    }

    @PutMapping("/{id}/cancel")
    public ResponseEntity<ScanDTO> cancelScan(@PathVariable Long id) {
        return ResponseEntity.ok(scanService.cancelScan(id));
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<Void> deleteScan(@PathVariable Long id) {
        scanService.deleteScan(id);
        return ResponseEntity.noContent().build();
    }

    @GetMapping("/count/status/{status}")
    public ResponseEntity<Long> countScansByStatus(@PathVariable Scan.ScanStatus status) {
        return ResponseEntity.ok(scanService.countScansByStatus(status));
    }
}
