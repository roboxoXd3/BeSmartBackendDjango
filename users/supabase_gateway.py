"""
Thin wrapper around Supabase Auth calls made on behalf of the frontend (we are
the BFF in front of Supabase). Every call goes through `call_supabase`, which
turns Supabase failures into a `SupabaseAuthError` (a DRF APIException), so
views can just let it propagate and the client gets `{"error": "..."}` with a
sensible status code.
"""
from django.conf import settings
from rest_framework.exceptions import APIException
from supabase import AuthError, create_client

from besmart_backend.utils.logger import get_logger

from .authentication import get_supabase_client, server_client_options

logger = get_logger(__name__)

# Supabase error codes -> the message we show. Anything unlisted gets the default,
# so raw Supabase messages never reach the client (they're still logged).
AUTH_ERROR_MESSAGES = {
    "invalid_credentials": "Invalid email or password.",
    "email_not_confirmed": "Please confirm your email address before logging in.",
    "user_banned": "This account has been disabled.",
    "refresh_token_not_found": "Session expired. Please log in again.",
    "refresh_token_already_used": "Session expired. Please log in again.",
    "session_not_found": "Session expired. Please log in again.",
    "email_exists": "A user with this email already exists.",
    "user_already_exists": "A user with this email already exists.",
    "email_address_invalid": "This email address is not allowed.",
    "signup_disabled": "Sign ups are currently disabled.",
    "same_password": "New password must be different from the current password.",
    "user_not_found": "User not found.",
    "reauthentication_needed": "Please confirm it's you: log in again and retry.",
}
# For these the Supabase message itself is safe and more useful (e.g. which
# password rule failed), so it's passed through.
PASSTHROUGH_CODES = {"weak_password", "validation_failed"}
DEFAULT_AUTH_ERROR = "Authentication failed."


class SupabaseAuthError(APIException):
    def __init__(self, message, status_code, code=None):
        self.status_code = status_code
        self.supabase_code = code
        super().__init__({"error": message})


def get_supabase_admin_client():
    """Client using the service-role key, for admin-only Auth APIs."""
    key = getattr(settings, 'SUPABASE_SERVICE_ROLE_KEY', None)
    if not settings.SUPABASE_URL or not key:
        logger.error("supabase_admin_misconfigured", error="SUPABASE_SERVICE_ROLE_KEY not set")
        raise SupabaseAuthError("Authentication service is not configured.", 503)
    return create_client(settings.SUPABASE_URL, key, options=server_client_options())


def call_supabase(event, fn, *, admin=False, client_error_status=401):
    """
    Run `fn(client)` against Supabase Auth and return its result.

    Supabase 4xx errors become `client_error_status` (401 for login-type calls,
    400 for data-changing calls), 429 stays 429, and 5xx / network failures
    become 502. Raises SupabaseAuthError.
    """
    if admin:
        client = get_supabase_admin_client()
    else:
        try:
            client = get_supabase_client()
        except ValueError as e:
            logger.error(f"{event}_misconfigured", error=str(e))
            raise SupabaseAuthError("Authentication service is not configured.", 503)

    try:
        return fn(client)
    except AuthError as e:
        # AuthApiError plus the SDK's own subclasses (AuthWeakPasswordError, ...).
        # No status (AuthUnknownError) or 0 (AuthRetryableError) means a network failure.
        code = getattr(e, "code", None)
        upstream_status = getattr(e, "status", None) or 502
        logger.warning(f"{event}_failed", reason=code or type(e).__name__, upstream_status=upstream_status, error=str(e))
        if upstream_status == 429:
            raise SupabaseAuthError("Too many attempts. Please wait a moment and try again.", 429, code)
        if upstream_status >= 500:
            raise SupabaseAuthError("Authentication service is unavailable. Please try again.", 502, code)
        if code in PASSTHROUGH_CODES:
            message = str(e)
        else:
            message = AUTH_ERROR_MESSAGES.get(code, DEFAULT_AUTH_ERROR)
        raise SupabaseAuthError(message, client_error_status, code)
    except SupabaseAuthError:
        raise
    except Exception as e:
        logger.error(f"{event}_error", error=str(e), error_type=type(e).__name__)
        raise SupabaseAuthError("Authentication service is unavailable. Please try again.", 502)
