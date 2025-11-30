package com.autoshield.dto;

import com.autoshield.entity.Scan;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.Map;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ScanRequestDTO {
    @NotNull(message = "Scan type is required")
    private Scan.ScanType type;

    @NotBlank(message = "Target is required")
    private String target;

    private String scanProfile;

    private Map<String, Object> parameters;
}
