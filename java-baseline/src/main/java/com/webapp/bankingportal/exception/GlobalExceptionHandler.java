package com.webapp.bankingportal.exception;

import com.fasterxml.jackson.databind.exc.InvalidDefinitionException;
import com.fasterxml.jackson.databind.exc.UnrecognizedPropertyException;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.http.converter.HttpMessageConversionException;
import org.springframework.http.converter.HttpMessageNotReadableException;
import org.springframework.security.authentication.BadCredentialsException;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ControllerAdvice;
import org.springframework.web.bind.annotation.ExceptionHandler;

import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.Map;

@ControllerAdvice
public class GlobalExceptionHandler {

    @ExceptionHandler(UnrecognizedPropertyException.class)
    public ResponseEntity<Map<String, String>> handleUnrecognizedProperty(UnrecognizedPropertyException ex) {
        Map<String, String> error = new HashMap<>();
        error.put("error", "Extra field detected: " + ex.getPropertyName());
        return new ResponseEntity<>(error, HttpStatus.BAD_REQUEST);
    }

    // 2. Specific Jackson Definition/Conversion Errors
    @ExceptionHandler({
            InvalidDefinitionException.class,
            HttpMessageConversionException.class
    })
    public ResponseEntity<Map<String, String>> handleJsonMappingErrors(Exception ex) {
        Map<String, String> error = new HashMap<>();
        String message = "Invalid request structure";

        if (ex.getMessage() != null && ex.getMessage().contains("Duplicate field")) {
            message = "Duplicate field detected in request body";
        }
        error.put("error", message);
        return new ResponseEntity<>(error, HttpStatus.BAD_REQUEST);
    }

    // 3. PRIORITY 3: Validation Errors (e.g., @NotBlank, @Email)
    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<Map<String, Object>> handleValidationExceptions(MethodArgumentNotValidException ex) {
        // LinkedHashMap preserves the order of insertion
        Map<String, String> fieldErrors = new LinkedHashMap<>();

        ex.getBindingResult().getFieldErrors().forEach(error -> {
            fieldErrors.put(error.getField(), error.getDefaultMessage());
        });

        Map<String, Object> response = new LinkedHashMap<>();
        response.put("errors", fieldErrors);

        return new ResponseEntity<>(response, HttpStatus.BAD_REQUEST);
    }

    @ExceptionHandler(FundTransferException.class)
    public ResponseEntity<Map<String, String>> handleFundTransferException(FundTransferException ex) {
        Map<String, String> response = new HashMap<>();
        response.put("error", ex.getMessage());
        return new ResponseEntity<>(response, HttpStatus.BAD_REQUEST);
    }

    @ExceptionHandler(InsufficientBalanceException.class)
    public ResponseEntity<Map<String, String>> handleInsufficientBalance(InsufficientBalanceException ex) {
        Map<String, String> response = new HashMap<>();
        response.put("error", ex.getMessage());
        return new ResponseEntity<>(response, HttpStatus.BAD_REQUEST);
    }

    @ExceptionHandler(InvalidAmountException.class)
    public ResponseEntity<Map<String, String>> handleInvalidAmount(InvalidAmountException ex) {
        Map<String, String> response = new HashMap<>();
        response.put("error", ex.getMessage());
        return new ResponseEntity<>(response, HttpStatus.BAD_REQUEST);
    }

    // 4. PRIORITY 4: Security & Unauthorized Access
    @ExceptionHandler({
            UnauthorizedException.class,
            BadCredentialsException.class,
            InvalidTokenException.class
    })
    public ResponseEntity<Map<String, String>> handleUnauthorizedAccess(Exception ex) {
        Map<String, String> error = new HashMap<>();
        String message = (ex instanceof BadCredentialsException) ? "Invalid identifier or password" : ex.getMessage();
        error.put("error", message);
        return new ResponseEntity<>(error, HttpStatus.UNAUTHORIZED);
    }

    // 5. PRIORITY 5: Business Logic Errors (User Invalid, Not Found)
    @ExceptionHandler({
            UserInvalidException.class,
            NotFoundException.class,
            IllegalArgumentException.class
    })
    public ResponseEntity<Map<String, String>> handleBusinessErrors(RuntimeException ex) {
        Map<String, String> error = new HashMap<>();
        error.put("error", ex.getMessage());

        HttpStatus status = (ex instanceof NotFoundException) ? HttpStatus.NOT_FOUND : HttpStatus.BAD_REQUEST;
        return new ResponseEntity<>(error, status);
    }

    // Fixes the 500 error for missing/invalid PIN formats
    @ExceptionHandler(InvalidPinException.class)
    public ResponseEntity<Map<String, String>> handleInvalidPin(InvalidPinException ex) {
        Map<String, String> error = new HashMap<>();
        error.put("error", ex.getMessage());
        return new ResponseEntity<>(error, HttpStatus.BAD_REQUEST); // Returns 400
    }

    // Handles the Duplicate PIN case (Scenario 2)
    @ExceptionHandler(ResourceAlreadyExistsException.class)
    public ResponseEntity<Map<String, String>> handleConflict(ResourceAlreadyExistsException ex) {
        Map<String, String> error = new HashMap<>();
        error.put("error", ex.getMessage());
        return new ResponseEntity<>(error, HttpStatus.CONFLICT); // Returns 409
    }

    // For Scenarios 2, 12, 13
    @ExceptionHandler(UserAlreadyExistsException.class)
    public ResponseEntity<Map<String, String>> handleUserExists(UserAlreadyExistsException ex) {
        return ResponseEntity.status(HttpStatus.BAD_REQUEST)
                .body(Map.of("error", ex.getMessage()));
    }

    // For Scenario 10 & 14
    @ExceptionHandler({InvalidPasswordException.class, InvalidPhoneNumberException.class})
    public ResponseEntity<Map<String, String>> handleUserInvalid(RuntimeException ex) {
        return ResponseEntity.status(HttpStatus.BAD_REQUEST)
                .body(Map.of("error", ex.getMessage()));
    }


    // 6. GENERAL Syntax Errors (Lower Priority)
    @ExceptionHandler(HttpMessageNotReadableException.class)
    public ResponseEntity<Map<String, String>> handleMalformedJson(HttpMessageNotReadableException ex) {
        Map<String, String> error = new HashMap<>();

        // Check if the actual cause of the "Unreadable" error is an "Unrecognized Property"
        if (ex.getCause() instanceof com.fasterxml.jackson.databind.exc.UnrecognizedPropertyException unrecognized) {
            error.put("error", "Extra field detected: " + unrecognized.getPropertyName());
        }
        // Check if it's a duplicate field error
        else if (ex.getMessage() != null && ex.getMessage().contains("Duplicate field")) {
            error.put("error", "Duplicate field detected in request body");
        }
        // Default to the general message
        else {
            error.put("error", "Malformed JSON or missing request body");
        }

        return new ResponseEntity<>(error, HttpStatus.BAD_REQUEST);
    }

    // 7. Global Catch-All
    @ExceptionHandler(Exception.class)
    public ResponseEntity<Map<String, String>> handleGlobalException(Exception ex) {
        Map<String, String> error = new HashMap<>();
        error.put("error", "An unexpected error occurred: " + ex.getMessage());
        return new ResponseEntity<>(error, HttpStatus.INTERNAL_SERVER_ERROR);
    }
}