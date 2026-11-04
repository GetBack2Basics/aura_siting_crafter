"""Pre-upload publish gate for the public GCS bucket.

The bucket gs://aura-siting-crafter-geolibre-app is public-read, so anything uploaded is public.
Every upload path (ingest, tile build, export) must call `assert_publishable` first.
"""

import os
import re

FORBIDDEN_NAME_PATTERNS = (
    r"(^|/)\.env($|\.)",
    r"credentials?.*\.json$",
    r"application_default_credentials\.json$",
    r"service[-_]?account.*\.json$",
    r"\.pem$",
    r"\.key$",
    r"(^|/)telemetry_.*\.json$",
)


class PublishBlocked(Exception):
    """Raised when a dataset or file must not be placed in the public bucket."""


def assert_publishable(entry: dict) -> None:
    """Block publication unless the manifest explicitly verifies that redistribution is allowed."""
    key = entry.get("dataset_key", "<unknown>")
    licence = entry.get("licence") or {}
    if licence.get("redistribution") is not True:
        raise PublishBlocked(
            f"{key}: licence.redistribution is {licence.get('redistribution')!r}; "
            "it must be verified as true (with licence name/url) before uploading to the public bucket."
        )
    if entry.get("access") != "public":
        raise PublishBlocked(f"{key}: access is {entry.get('access')!r}, not 'public'.")
    if not licence.get("attribution") and licence.get("name") not in (None, "public-domain"):
        raise PublishBlocked(f"{key}: licence has no attribution string recorded.")


def assert_safe_object_name(object_name: str) -> None:
    """Block credential-like or telemetry files by name."""
    normalized = object_name.replace(os.sep, "/")
    for pattern in FORBIDDEN_NAME_PATTERNS:
        if re.search(pattern, normalized, flags=re.IGNORECASE):
            raise PublishBlocked(f"{object_name}: file name matches a forbidden pattern ({pattern}).")

