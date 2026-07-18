"""
Scanner check modules for passive vulnerability detection.

Each module exports a list of check functions that accept
(response, parsed_url, findings) and append findings in-place.
"""
from .injection import INJECTION_CHECKS
from .access_control import ACCESS_CONTROL_CHECKS
from .auth import AUTH_CHECKS
from .app_security import APP_SECURITY_CHECKS
from .redirect import REDIRECT_CHECKS
from .bypass_403 import BYPASS_403_CHECKS
from .race_condition import RACE_CONDITION_CHECKS
from .sensitive_files import SENSITIVE_FILES_CHECKS
from .headers_analysis import HEADERS_ANALYSIS_CHECKS
from .dns_extended import DNS_EXTENDED_CHECKS
from .cors_reflection import CORS_REFLECTION_CHECKS
from .source_maps import SOURCE_MAP_CHECKS
from .js_security import JS_SECURITY_CHECKS
from .data_exposure import DATA_EXPOSURE_CHECKS
from .discovery import DISCOVERY_CHECKS
from .cookie_security import COOKIE_SECURITY_CHECKS
from .jwt_deep import JWT_DEEP_CHECKS
from .error_disclosure import ERROR_DISCLOSURE_CHECKS
from .tls_checks import TLS_CHECKS
from .broken_links import BROKEN_LINKS_CHECKS
from .webshells import WEBSHELL_CHECKS
from .http_methods import HTTP_METHODS_CHECKS
from .backup_files import BACKUP_FILES_CHECKS
from .lfi_probing import LFI_CHECKS
from .idor_detection import IDOR_CHECKS
from .rate_limit import RATE_LIMIT_CHECKS
from .reflected_xss import REFLECTED_XSS_CHECKS
from .headers_extra import HEADERS_EXTRA_CHECKS

ALL_CHECKS = (
    INJECTION_CHECKS
    + ACCESS_CONTROL_CHECKS
    + AUTH_CHECKS
    + APP_SECURITY_CHECKS
    + REDIRECT_CHECKS
    + BYPASS_403_CHECKS
    + RACE_CONDITION_CHECKS
    + SENSITIVE_FILES_CHECKS
    + HEADERS_ANALYSIS_CHECKS
    + DNS_EXTENDED_CHECKS
    + CORS_REFLECTION_CHECKS
    + SOURCE_MAP_CHECKS
    + JS_SECURITY_CHECKS
    + DATA_EXPOSURE_CHECKS
    + DISCOVERY_CHECKS
    + COOKIE_SECURITY_CHECKS
    + JWT_DEEP_CHECKS
    + ERROR_DISCLOSURE_CHECKS
    + TLS_CHECKS
    + BROKEN_LINKS_CHECKS
    + WEBSHELL_CHECKS
    + HTTP_METHODS_CHECKS
    + BACKUP_FILES_CHECKS
    + LFI_CHECKS
    + IDOR_CHECKS
    + RATE_LIMIT_CHECKS
    + REFLECTED_XSS_CHECKS
    + HEADERS_EXTRA_CHECKS
)
