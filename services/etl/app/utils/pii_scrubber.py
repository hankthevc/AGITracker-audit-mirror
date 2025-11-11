"""PII scrubbing utilities for GDPR compliance (Sprint 8.2).

This module provides utilities to detect and scrub Personally Identifiable Information (PII)
from various data sources including logs, database records, and API responses.
"""

import re
import hashlib
from typing import Any, Dict, List


# PII Detection Patterns
EMAIL_PATTERN = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
PHONE_PATTERN = re.compile(r'\b(\+\d{1,3}[\s-]?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}\b')
SSN_PATTERN = re.compile(r'\b\d{3}-\d{2}-\d{4}\b')
CREDIT_CARD_PATTERN = re.compile(r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b')
IP_ADDRESS_PATTERN = re.compile(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b')


def anonymize_ip_address(ip: str) -> str:
    """
    Anonymize an IP address by zeroing the last octet.
    
    This is the standard approach for GDPR compliance while maintaining
    some geographic relevance for analytics.
    
    Args:
        ip: IPv4 address string (e.g., "192.168.1.100")
        
    Returns:
        Anonymized IP with last octet set to 0 (e.g., "192.168.1.0")
    
    Examples:
        >>> anonymize_ip_address("192.168.1.100")
        "192.168.1.0"
        >>> anonymize_ip_address("10.0.0.1")
        "10.0.0.0"
    """
    parts = ip.split(".")
    if len(parts) == 4:
        parts[-1] = "0"
        return ".".join(parts)
    return ip


def hash_pii(value: str, salt: str = "") -> str:
    """
    Hash a PII value for storage when the original value is not needed.
    
    Uses SHA-256 with optional salt for one-way hashing.
    
    Args:
        value: Value to hash
        salt: Optional salt to add to the hash
        
    Returns:
        Hex-encoded SHA-256 hash
    """
    salted_value = f"{value}{salt}"
    return hashlib.sha256(salted_value.encode()).hexdigest()


def redact_email(email: str) -> str:
    """
    Redact an email address for display purposes.
    
    Shows first character and domain, redacts the rest.
    
    Args:
        email: Email address to redact
        
    Returns:
        Redacted email (e.g., "j****@example.com")
    
    Examples:
        >>> redact_email("john.doe@example.com")
        "j****@example.com"
    """
    if "@" not in email:
        return "***"
    
    local, domain = email.split("@", 1)
    if len(local) <= 1:
        return f"*@{domain}"
    
    return f"{local[0]}****@{domain}"


def scrub_pii_from_text(text: str) -> str:
    """
    Scrub PII from a text string by replacing with placeholders.
    
    Detects and replaces:
    - Email addresses -> [EMAIL_REDACTED]
    - Phone numbers -> [PHONE_REDACTED]
    - SSN -> [SSN_REDACTED]
    - Credit cards -> [CC_REDACTED]
    - IP addresses -> [IP_REDACTED]
    
    Args:
        text: Text to scrub
        
    Returns:
        Scrubbed text with PII replaced
    """
    if not text:
        return text
    
    # Replace PII patterns with placeholders
    text = EMAIL_PATTERN.sub("[EMAIL_REDACTED]", text)
    text = PHONE_PATTERN.sub("[PHONE_REDACTED]", text)
    text = SSN_PATTERN.sub("[SSN_REDACTED]", text)
    text = CREDIT_CARD_PATTERN.sub("[CC_REDACTED]", text)
    text = IP_ADDRESS_PATTERN.sub("[IP_REDACTED]", text)
    
    return text


def detect_pii_in_text(text: str) -> List[Dict[str, Any]]:
    """
    Detect PII in text without modifying it.
    
    Returns a list of detected PII items with type and position.
    
    Args:
        text: Text to analyze
        
    Returns:
        List of dictionaries with 'type', 'value', 'start', 'end' keys
    """
    if not text:
        return []
    
    findings = []
    
    # Check for emails
    for match in EMAIL_PATTERN.finditer(text):
        findings.append({
            "type": "email",
            "value": match.group(),
            "start": match.start(),
            "end": match.end()
        })
    
    # Check for phone numbers
    for match in PHONE_PATTERN.finditer(text):
        findings.append({
            "type": "phone",
            "value": match.group(),
            "start": match.start(),
            "end": match.end()
        })
    
    # Check for SSN
    for match in SSN_PATTERN.finditer(text):
        findings.append({
            "type": "ssn",
            "value": match.group(),
            "start": match.start(),
            "end": match.end()
        })
    
    # Check for credit cards
    for match in CREDIT_CARD_PATTERN.finditer(text):
        findings.append({
            "type": "credit_card",
            "value": match.group(),
            "start": match.start(),
            "end": match.end()
        })
    
    # Check for IP addresses
    for match in IP_ADDRESS_PATTERN.finditer(text):
        findings.append({
            "type": "ip_address",
            "value": match.group(),
            "start": match.start(),
            "end": match.end()
        })
    
    return findings


def audit_database_for_pii(db_session) -> Dict[str, Any]:
    """
    Audit database tables for PII content.
    
    Checks all text fields in major tables for potential PII.
    
    Args:
        db_session: SQLAlchemy database session
        
    Returns:
        Dictionary with audit results per table
    """
    from app.models import Event, Roadmap, Signpost, Source
    
    audit_results = {
        "timestamp": None,
        "tables_checked": 0,
        "pii_found": False,
        "findings": []
    }
    
    # Tables to check (add more as needed)
    tables_to_check = [
        (Event, ["title", "summary", "content_text", "author", "byline"]),
        (Roadmap, ["description", "summary", "author"]),
        (Signpost, ["description", "short_explainer"]),
        (Source, ["url"]),  # URLs can contain emails
    ]
    
    for model, fields in tables_to_check:
        audit_results["tables_checked"] += 1
        
        # Sample records from each table
        records = db_session.query(model).limit(100).all()
        
        for record in records:
            for field in fields:
                value = getattr(record, field, None)
                if value and isinstance(value, str):
                    pii_items = detect_pii_in_text(value)
                    if pii_items:
                        audit_results["pii_found"] = True
                        audit_results["findings"].append({
                            "table": model.__tablename__,
                            "record_id": record.id,
                            "field": field,
                            "pii_types": [item["type"] for item in pii_items],
                            "count": len(pii_items)
                        })
    
    from datetime import datetime, timezone
    audit_results["timestamp"] = datetime.now(timezone.utc).isoformat()
    
    return audit_results


def scrub_dict_values(data: Dict[str, Any], keys_to_scrub: List[str] = None) -> Dict[str, Any]:
    """
    Recursively scrub PII from dictionary values.
    
    Useful for scrubbing API request/response data.
    
    Args:
        data: Dictionary to scrub
        keys_to_scrub: List of key names to always scrub (e.g., ["email", "phone"])
        
    Returns:
        Scrubbed dictionary
    """
    if keys_to_scrub is None:
        keys_to_scrub = ["email", "phone", "ssn", "credit_card", "password"]
    
    scrubbed = {}
    
    for key, value in data.items():
        # Always scrub specific keys
        if key.lower() in keys_to_scrub:
            scrubbed[key] = "[REDACTED]"
        # Recursively handle nested dicts
        elif isinstance(value, dict):
            scrubbed[key] = scrub_dict_values(value, keys_to_scrub)
        # Handle lists
        elif isinstance(value, list):
            scrubbed[key] = [
                scrub_dict_values(item, keys_to_scrub) if isinstance(item, dict) else item
                for item in value
            ]
        # Scrub text fields
        elif isinstance(value, str):
            scrubbed[key] = scrub_pii_from_text(value)
        else:
            scrubbed[key] = value
    
    return scrubbed


# Data Retention Utilities

def should_archive_record(created_at, retention_days: int = 365) -> bool:
    """
    Check if a record should be archived based on age.
    
    Args:
        created_at: Record creation timestamp
        retention_days: Number of days to retain (default 1 year)
        
    Returns:
        True if record is older than retention period
    """
    from datetime import datetime, timedelta, timezone
    
    if not created_at:
        return False
    
    # Make timezone-aware if needed
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)
    
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=retention_days)
    return created_at < cutoff_date


def get_retention_policy() -> Dict[str, int]:
    """
    Get data retention policies for different data types.
    
    Returns:
        Dictionary mapping data type to retention period in days
    """
    return {
        "events": 730,  # 2 years
        "logs": 30,  # 30 days
        "api_keys": 365,  # 1 year inactive
        "digests": -1,  # Keep forever
        "analysis": 730,  # 2 years
        "ingest_runs": 90,  # 3 months
    }
