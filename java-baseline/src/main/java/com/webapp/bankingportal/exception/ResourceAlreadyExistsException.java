package com.webapp.bankingportal.exception;

/**
 * Exception thrown when a resource (like a PIN) already exists.
 * This allows the GlobalExceptionHandler to return a 409 Conflict status.
 */
public class ResourceAlreadyExistsException extends RuntimeException {
    public ResourceAlreadyExistsException(String message) {
        super(message);
    }
}