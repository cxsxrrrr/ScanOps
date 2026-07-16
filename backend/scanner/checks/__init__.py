"""
Scanner check modules for passive vulnerability detection.

Each module exports a list of check functions that accept
(response, parsed_url, findings) and append findings in-place.
"""
from .injection import INJECTION_CHECKS
from .access_control import ACCESS_CONTROL_CHECKS
from .auth import AUTH_CHECKS
from .app_security import APP_SECURITY_CHECKS
from .headers_extra import HEADERS_EXTRA_CHECKS

ALL_CHECKS = (
    INJECTION_CHECKS + ACCESS_CONTROL_CHECKS + AUTH_CHECKS
    + APP_SECURITY_CHECKS + HEADERS_EXTRA_CHECKS
)
