"""
Recovery policies for DocuSure.

AUTO:
    Safe deterministic recovery may be attempted.

HUMAN:
    The agent must stop and ask a human.

STOP:
    The agent must not attempt an automatic recovery.
"""


RECOVERY_POLICIES = {

    # ========================================================
    # AUTOMATIC RECOVERY
    # ========================================================

    "FILE_TOO_LARGE": "AUTO",

    "INVALID_FILE_TYPE": "AUTO",

    "TEMPORARY_SERVER_ERROR": "AUTO",

    "FORM_VALUE_NOT_RETAINED": "AUTO",


    # ========================================================
    # HUMAN REVIEW
    # ========================================================

    "DOB_CONFLICT": "HUMAN",

    "NAME_CONFLICT": "HUMAN",

    "OTP_REQUIRED": "HUMAN",

    "CAPTCHA": "HUMAN",


    # ========================================================
    # STOP
    # ========================================================

    "UNKNOWN_STATE": "STOP",
}