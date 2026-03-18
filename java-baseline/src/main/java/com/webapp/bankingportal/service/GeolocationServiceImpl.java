package com.webapp.bankingportal.service;

import java.net.InetAddress;
import java.net.UnknownHostException;
import java.util.Map;
import java.util.concurrent.CompletableFuture;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestClientException;
import org.springframework.web.client.RestTemplate;

import com.webapp.bankingportal.dto.GeolocationResponse;
import com.webapp.bankingportal.exception.GeolocationException;

import lombok.val;
import lombok.extern.slf4j.Slf4j;

@Service
@Slf4j
public class GeolocationServiceImpl implements GeolocationService {

    @Value("${geo.api.url}")
    private String apiUrl;

    @Value("${geo.api.key}")
    private String apiKey;

    @Override
    @Async
    public CompletableFuture<GeolocationResponse> getGeolocation(String ip) {
        val future = new CompletableFuture<GeolocationResponse>();

        try {
            // Validate and check for Localhost
            InetAddress address = InetAddress.getByName(ip);

            if (address.isLoopbackAddress() || "0:0:0:0:0:0:0:1".equals(ip)) {
                log.info("Local environment detected for IP: {}. Skipping external API call.", ip);

                GeolocationResponse localResponse = new GeolocationResponse();

                // Initialize City with the Map required by your DTO
                GeolocationResponse.City city = new GeolocationResponse.City();
                city.setNames(Map.of("en", "Localhost"));
                localResponse.setCity(city);

                // Initialize Country with the Map required by your DTO
                GeolocationResponse.Country country = new GeolocationResponse.Country();
                country.setNames(Map.of("en", "Internal Network"));
                localResponse.setCountry(country);

                future.complete(localResponse);
                return future;
            }

            log.info("Getting geolocation for IP: {}", ip);

            // Call geolocation API
            val url = String.format("%s/%s/?token=%s", apiUrl, ip, apiKey);
            val response = new RestTemplate().getForObject(url, GeolocationResponse.class);

            if (response == null) {
                log.error("Failed to get geolocation for IP: {}", ip);
                future.completeExceptionally(new GeolocationException(
                        "Failed to get geolocation for IP: " + ip));
            } else {
                future.complete(response);
            }

        } catch (UnknownHostException e) {
            log.error("Invalid IP address: {}", ip, e);
            future.completeExceptionally(e);
        } catch (RestClientException e) {
            log.error("Failed to get geolocation for IP: {}", ip, e);
            future.completeExceptionally(e);
        }

        return future;
    }
}