"""Mock VirusTotal file report lookup by SHA-256 hash."""

import hashlib
from dataclasses import dataclass

from config import get_settings

# Deterministic mock: this payload hashes to a "malicious" value in our stub rules.
_MALICIOUS_SAMPLE = b"MALWARE_SAMPLE_PLACEHOLDER"


@dataclass
class VirusTotalReport:
    sha256: str
    flagged: bool
    positives: int
    total: int
    mock: bool = True


def check_hash_virustotal(sha256_hash: str) -> VirusTotalReport:
    """
    Mock VirusTotal v3 file report for a hash.
    Uses VIRUSTOTAL_API_KEY from settings (logged only in mock mode).
    """
    settings = get_settings()
    _ = settings.virustotal_api_key  # Reserved for real HTTP integration.

    malicious_reference = hashlib.sha256(_MALICIOUS_SAMPLE).hexdigest()
    flagged = sha256_hash == malicious_reference

    return VirusTotalReport(
        sha256=sha256_hash,
        flagged=flagged,
        positives=5 if flagged else 0,
        total=70,
    )
