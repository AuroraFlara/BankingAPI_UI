package com.webapp.bankingportal.config;

import jakarta.servlet.*;
import jakarta.servlet.http.HttpServletRequest;
import org.springframework.stereotype.Component;
import java.io.IOException;

@Component
public class PerformanceFilter implements Filter {
    @Override
    public void doFilter(ServletRequest request, ServletResponse response, FilterChain chain)
            throws IOException, ServletException {
        // Record the start time in nanoseconds
        request.setAttribute("startTime", System.nanoTime());
        chain.doFilter(request, response);
    }
}