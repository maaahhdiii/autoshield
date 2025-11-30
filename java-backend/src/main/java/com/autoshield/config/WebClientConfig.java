package com.autoshield.config;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.client.reactive.ReactorClientHttpConnector;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.netty.http.client.HttpClient;

import java.time.Duration;

@Configuration
public class WebClientConfig {

    @Value("${autoshield.mcp.python-ai.url}")
    private String pythonAiUrl;

    @Value("${autoshield.mcp.kali-mcp.url}")
    private String kaliMcpUrl;

    @Value("${autoshield.mcp.python-ai.timeout:30000}")
    private int pythonAiTimeout;

    @Value("${autoshield.mcp.kali-mcp.timeout:60000}")
    private int kaliMcpTimeout;

    @Bean
    public WebClient pythonAiWebClient() {
        HttpClient httpClient = HttpClient.create()
            .responseTimeout(Duration.ofMillis(pythonAiTimeout));

        return WebClient.builder()
            .baseUrl(pythonAiUrl)
            .clientConnector(new ReactorClientHttpConnector(httpClient))
            .build();
    }

    @Bean
    public WebClient kaliMcpWebClient() {
        HttpClient httpClient = HttpClient.create()
            .responseTimeout(Duration.ofMillis(kaliMcpTimeout));

        return WebClient.builder()
            .baseUrl(kaliMcpUrl)
            .clientConnector(new ReactorClientHttpConnector(httpClient))
            .build();
    }
}
