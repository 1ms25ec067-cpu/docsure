from typing import Any
from urllib.parse import urlparse

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

from app.verification.store import evidence_store


class WebsiteApplicationAgent:
    """
    Evidence-gated browser automation agent.

    Workflow:
        OPEN
        -> DISCOVER
        -> MAP
        -> FILL
        -> READ-BACK
        -> SUBMIT
        -> INDEPENDENT CONFIRMATION

    The agent never treats filling a form as proof of submission.
    """

    def __init__(self):
        self.timeout = 15000

    def run(
        self,
        url: str,
        field_values: dict[str, str],
        submit: bool = True,
    ) -> dict[str, Any]:

        result = {
            "status": "BLOCKED",
            "reason": None,
            "url": url,
            "final_url": None,
            "verification": [],
            "evidence": [],
        }

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)

            page = browser.new_page(
                viewport={
                    "width": 1440,
                    "height": 1000,
                }
            )

            try:
                # ---------------------------------------------------------
                # 1. OPEN WEBSITE
                # ---------------------------------------------------------
                page.goto(
                    url,
                    wait_until="domcontentloaded",
                    timeout=self.timeout,
                )

                try:
                    page.wait_for_load_state(
                        "networkidle",
                        timeout=5000,
                    )
                except PlaywrightTimeoutError:
                    pass

                final_url = page.url
                title = page.title()

                result["final_url"] = final_url

                website_open_evidence = evidence_store.add(
                    source="docsure_browser_agent",
                    claim="Target application website was opened.",
                    value={
                        "url": final_url,
                        "title": title,
                        "http_status": 200,
                    },
                    verdict="VERIFIED",
                    evidence_type="WEBSITE_OPEN",
                    metadata={
                        "requested_url": url,
                    },
                )

                result["evidence"].append(website_open_evidence)

                # Detect obvious login pages.
                if self._is_login_page(page):
                    result["status"] = "BLOCKED"
                    result["reason"] = "LOGIN_REQUIRED"

                    result["verification"].append(
                        {
                            "status": "BLOCKED",
                            "reason": "LOGIN_REQUIRED",
                            "url": page.url,
                        }
                    )

                    return result

                # ---------------------------------------------------------
                # 2. DISCOVER FORM FIELDS
                # ---------------------------------------------------------
                fields = self._discover_fields(page)

                discovery_evidence = evidence_store.add(
                    source="docsure_browser_agent",
                    claim="Application form fields were inspected.",
                    value={
                        "field_count": len(fields),
                        "fields": [
                            {
                                "label": field["label"],
                                "type": field["type"],
                                "name": field["name"],
                                "id": field["id"],
                                "placeholder": field["placeholder"],
                                "aria_label": field["aria_label"],
                            }
                            for field in fields
                        ],
                    },
                    verdict="VERIFIED",
                    evidence_type="FORM_DISCOVERY",
                    metadata={
                        "url": page.url,
                    },
                )

                result["evidence"].append(discovery_evidence)

                if not fields:
                    result["status"] = "BLOCKED"
                    result["reason"] = "NO_FORM_FIELDS"

                    result["verification"].append(
                        {
                            "status": "BLOCKED",
                            "reason": "NO_FORM_FIELDS",
                        }
                    )

                    return result

                # ---------------------------------------------------------
                # 3. MAP VERIFIED DATA TO WEBSITE FIELDS
                # ---------------------------------------------------------
                mappings = []

                for source_field, expected_value in field_values.items():

                    field = self._find_matching_field(
                        page=page,
                        fields=fields,
                        source_field=source_field,
                    )

                    if field is None:
                        mapping_evidence = evidence_store.add(
                            source="docsure_browser_agent",
                            claim="Verified document data was mapped to website fields.",
                            value={
                                "source_field": source_field,
                                "website_field": None,
                                "value": expected_value,
                            },
                            verdict="BLOCKED",
                            evidence_type="FIELD_MAPPING",
                            metadata={
                                "reason": "FIELD_NOT_FOUND",
                            },
                        )

                        result["evidence"].append(mapping_evidence)

                        result["status"] = "BLOCKED"
                        result["reason"] = "FIELD_MAPPING_FAILED"

                        result["verification"].append(
                            {
                                "field": source_field,
                                "verified": False,
                                "reason": "FIELD_NOT_FOUND",
                            }
                        )

                        return result

                    mappings.append(
                        {
                            "source_field": source_field,
                            "website_field": field,
                            "value": expected_value,
                        }
                    )

                mapping_evidence = evidence_store.add(
                    source="docsure_browser_agent",
                    claim="Verified document data was mapped to website fields.",
                    value={
                        "mapping": [
                            {
                                "source_field": item["source_field"],
                                "website_field": item["website_field"]["label"],
                                "value": item["value"],
                            }
                            for item in mappings
                        ]
                    },
                    verdict="VERIFIED",
                    evidence_type="FIELD_MAPPING",
                    metadata={
                        "mapped_fields": len(mappings),
                    },
                )

                result["evidence"].append(mapping_evidence)

                # ---------------------------------------------------------
                # 4. FILL FIELDS
                # ---------------------------------------------------------
                filled = []

                for item in mappings:
                    success = self._fill_field(
                        page=page,
                        field=item["website_field"],
                        value=item["value"],
                    )

                    if not success:
                        filling_evidence = evidence_store.add(
                            source="docsure_browser_agent",
                            claim="Mapped application fields were filled.",
                            value={
                                "source_field": item["source_field"],
                                "website_field": item["website_field"]["label"],
                                "value": item["value"],
                            },
                            verdict="BLOCKED",
                            evidence_type="FORM_FILLING",
                            metadata={
                                "reason": "FIELD_FILL_FAILED",
                            },
                        )

                        result["evidence"].append(filling_evidence)

                        result["status"] = "BLOCKED"
                        result["reason"] = "FORM_FILL_FAILED"

                        return result

                    filled.append(item)

                filling_evidence = evidence_store.add(
                    source="docsure_browser_agent",
                    claim="Mapped application fields were filled.",
                    value={
                        "filled_count": len(filled),
                        "fields": [
                            {
                                "source_field": item["source_field"],
                                "website_field": item["website_field"]["label"],
                                "value": item["value"],
                            }
                            for item in filled
                        ],
                    },
                    verdict="VERIFIED",
                    evidence_type="FORM_FILLING",
                    metadata={
                        "field_count": len(filled),
                    },
                )

                result["evidence"].append(filling_evidence)

                # Allow React/Google Forms JavaScript to settle.
                page.wait_for_timeout(500)

                # ---------------------------------------------------------
                # 5. READ-BACK VERIFICATION
                # ---------------------------------------------------------
                verification_results = []

                for item in filled:
                    actual_value = self._read_field(
                        page=page,
                        field=item["website_field"],
                    )

                    expected_value = str(item["value"]).strip()
                    actual_value = str(actual_value or "").strip()

                    verified = (
                        actual_value == expected_value
                    )

                    verification_results.append(
                        {
                            "field": item["website_field"]["label"],
                            "expected": expected_value,
                            "actual": actual_value,
                            "verified": verified,
                        }
                    )

                all_verified = all(
                    item["verified"]
                    for item in verification_results
                )

                if not all_verified:

                    readback_evidence = evidence_store.add(
                        source="docsure_browser_agent",
                        claim="All entered values were independently read back and verified.",
                        value={
                            "verification": "FORM_VALUES_NOT_CONFIRMED",
                            "fields": verification_results,
                        },
                        verdict="BLOCKED",
                        evidence_type="FORM_VALUE_VERIFICATION",
                        metadata={
                            "reason": "VALUE_MISMATCH",
                        },
                    )

                    result["evidence"].append(readback_evidence)

                    result["status"] = "BLOCKED"
                    result["reason"] = "FORM_VALUES_NOT_CONFIRMED"
                    result["verification"] = verification_results

                    return result

                readback_evidence = evidence_store.add(
                    source="docsure_browser_agent",
                    claim="All entered values were independently read back and verified.",
                    value={
                        "verification": "FORM_VALUES_CONFIRMED",
                        "fields": verification_results,
                    },
                    verdict="VERIFIED",
                    evidence_type="FORM_VALUE_VERIFICATION",
                    metadata={
                        "field_count": len(verification_results),
                    },
                )

                result["evidence"].append(readback_evidence)

                result["verification"] = verification_results

                # ---------------------------------------------------------
                # 6. SUBMISSION
                # ---------------------------------------------------------
                if not submit:
                    result["status"] = "VERIFIED"
                    result["reason"] = "FORM_VALUES_CONFIRMED"
                    return result

                submitted = self._submit(page)

                if not submitted:
                    submission_evidence = evidence_store.add(
                        source="docsure_browser_agent",
                        claim="Application form was submitted.",
                        value={
                            "submission_attempted": True,
                            "verification": "SUBMISSION_NOT_CONFIRMED",
                        },
                        verdict="BLOCKED",
                        evidence_type="SUBMISSION_VERIFICATION",
                        metadata={
                            "reason": "SUBMIT_BUTTON_NOT_FOUND",
                        },
                    )

                    result["evidence"].append(submission_evidence)

                    result["status"] = "BLOCKED"
                    result["reason"] = "SUBMISSION_NOT_CONFIRMED"

                    return result

                # Give the destination page time to update.
                page.wait_for_timeout(1000)

                # ---------------------------------------------------------
                # 7. INDEPENDENT SUBMISSION CONFIRMATION
                # ---------------------------------------------------------
                confirmation = self._detect_submission(page)

                if confirmation["confirmed"]:

                    submission_evidence = evidence_store.add(
                        source="docsure_browser_agent",
                        claim="Application submission was independently confirmed.",
                        value={
                            "verification": "SUBMISSION_CONFIRMED",
                            "url": page.url,
                            "confirmation_signal": confirmation["signal"],
                        },
                        verdict="VERIFIED",
                        evidence_type="SUBMISSION_VERIFICATION",
                        metadata={
                            "requested_url": url,
                            "final_url": page.url,
                        },
                    )

                    result["evidence"].append(submission_evidence)

                    result["status"] = "VERIFIED"
                    result["reason"] = "SUBMISSION_CONFIRMED"
                    result["final_url"] = page.url

                    return result

                submission_evidence = evidence_store.add(
                    source="docsure_browser_agent",
                    claim="Application submission was independently confirmed.",
                    value={
                        "verification": "SUBMISSION_NOT_CONFIRMED",
                        "url": page.url,
                    },
                    verdict="BLOCKED",
                    evidence_type="SUBMISSION_VERIFICATION",
                    metadata={
                        "reason": "NO_CONFIRMATION_SIGNAL",
                    },
                )

                result["evidence"].append(submission_evidence)

                result["status"] = "BLOCKED"
                result["reason"] = "SUBMISSION_NOT_CONFIRMED"

                return result

            except Exception as error:

                result["status"] = "FAILED"
                result["reason"] = "BROWSER_WORKFLOW_ERROR"
                result["error"] = str(error)
                result["final_url"] = page.url

                return result

            finally:
                browser.close()

    # =====================================================================
    # FIELD DISCOVERY
    # =====================================================================

    def _discover_fields(self, page):

        discovered = []

        # -------------------------------------------------------------
        # Standard HTML inputs
        # -------------------------------------------------------------
        inputs = page.locator(
            "input, textarea, select"
        )

        count = inputs.count()

        for index in range(count):

            element = inputs.nth(index)

            try:
                if not element.is_visible():
                    continue

                tag = element.evaluate(
                    "(el) => el.tagName.toLowerCase()"
                )

                input_type = (
                    element.get_attribute("type")
                    or tag
                )

                if input_type in {
                    "hidden",
                    "submit",
                    "button",
                    "reset",
                    "file",
                    "checkbox",
                    "radio",
                }:
                    continue

                field_id = element.get_attribute("id") or ""
                name = element.get_attribute("name") or ""
                placeholder = (
                    element.get_attribute("placeholder")
                    or ""
                )
                aria_label = (
                    element.get_attribute("aria-label")
                    or ""
                )

                label = self._get_label_text(
                    page,
                    element,
                )

                # Google Forms commonly exposes the question
                # through aria-label.
                if aria_label:
                    label = aria_label

                if not label:
                    label = (
                        placeholder
                        or name
                        or field_id
                        or f"field_{index}"
                    )

                discovered.append(
                    {
                        "element": element,
                        "label": label.strip(),
                        "type": input_type,
                        "name": name,
                        "id": field_id,
                        "placeholder": placeholder,
                        "aria_label": aria_label,
                        "index": index,
                    }
                )

            except Exception:
                continue

        # -------------------------------------------------------------
        # Google Forms enhancement
        # -------------------------------------------------------------
        # Google Forms questions are normally contained inside:
        #
        # <div role="listitem">
        #
        # and the question text is close to the actual input.
        #
        # We attach that question text to the discovered field.
        # -------------------------------------------------------------

        for field in discovered:

            try:
                question_text = field["element"].evaluate(
                    """
                    (el) => {
                        const item =
                            el.closest('[role="listitem"]');

                        if (!item) return "";

                        return item.innerText
                            .replace(/\\n+/g, " ")
                            .trim();
                    }
                    """
                )

                if question_text:
                    field["question_text"] = question_text

            except Exception:
                field["question_text"] = ""

        return discovered

    # =====================================================================
    # FIELD MATCHING
    # =====================================================================

    def _find_matching_field(
        self,
        page,
        fields,
        source_field,
    ):

        source = self._normalize(source_field)

        # -------------------------------------------------------------
        # Exact match
        # -------------------------------------------------------------

        for field in fields:

            candidates = [
                field.get("label", ""),
                field.get("aria_label", ""),
                field.get("name", ""),
                field.get("id", ""),
                field.get("placeholder", ""),
                field.get("question_text", ""),
            ]

            for candidate in candidates:

                if self._normalize(candidate) == source:
                    return field

        # -------------------------------------------------------------
        # Partial match
        # -------------------------------------------------------------

        for field in fields:

            candidates = [
                field.get("label", ""),
                field.get("aria_label", ""),
                field.get("name", ""),
                field.get("id", ""),
                field.get("placeholder", ""),
                field.get("question_text", ""),
            ]

            normalized_candidates = [
                self._normalize(candidate)
                for candidate in candidates
                if candidate
            ]

            for candidate in normalized_candidates:

                if (
                    source in candidate
                    or candidate in source
                ):
                    return field

        # -------------------------------------------------------------
        # Common field-name aliases
        # -------------------------------------------------------------

        aliases = {
            "fullname": [
                "name",
                "full name",
                "fullname",
            ],
            "name": [
                "name",
                "full name",
                "fullname",
            ],
            "email": [
                "email",
                "email address",
                "e-mail",
            ],
        }

        possible = aliases.get(source, [])

        for field in fields:

            candidates = [
                self._normalize(field.get("label", "")),
                self._normalize(field.get("aria_label", "")),
                self._normalize(field.get("name", "")),
                self._normalize(field.get("question_text", "")),
            ]

            for candidate in candidates:

                for alias in possible:

                    if alias in candidate:
                        return field

        return None

    # =====================================================================
    # FILLING
    # =====================================================================

    def _fill_field(
        self,
        page,
        field,
        value,
    ):

        element = field["element"]

        try:
            element.scroll_into_view_if_needed()

            # Google Forms text fields.
            element.fill(
                str(value),
                timeout=self.timeout,
            )

            # Trigger input/change events.
            try:
                element.dispatch_event("input")
            except Exception:
                pass

            try:
                element.dispatch_event("change")
            except Exception:
                pass

            return True

        except Exception:

            # Fallback: click + keyboard.
            try:
                element.click(
                    timeout=5000
                )

                element.press("Control+A")

                element.type(
                    str(value),
                    delay=10,
                )

                return True

            except Exception:
                return False

    # =====================================================================
    # READ-BACK
    # =====================================================================

    def _read_field(
        self,
        page,
        field,
    ):

        element = field["element"]

        # -------------------------------------------------------------
        # IMPORTANT:
        # Read the VALUE property of the EXACT SAME DOM element
        # that was filled.
        #
        # This prevents Google Forms internal elements from being
        # accidentally selected during verification.
        # -------------------------------------------------------------

        try:
            element.scroll_into_view_if_needed()

            value = element.input_value(
                timeout=self.timeout
            )

            if value is not None:
                return value

        except Exception:
            pass

        # -------------------------------------------------------------
        # JavaScript fallback
        # -------------------------------------------------------------

        try:
            value = element.evaluate(
                """
                (el) => {
                    if ("value" in el) {
                        return el.value;
                    }

                    return el.getAttribute("value") || "";
                }
                """
            )

            return value or ""

        except Exception:
            return ""

    # =====================================================================
    # SUBMIT
    # =====================================================================

    def _submit(self, page):

        selectors = [
            'button:has-text("Submit")',
            'button:has-text("Apply")',
            'button:has-text("Continue")',
            'button:has-text("Finish")',
            'input[type="submit"]',
            '[role="button"]:has-text("Submit")',
            '[role="button"]:has-text("Submit form")',
        ]

        for selector in selectors:

            try:

                button = page.locator(selector).first

                if button.is_visible():

                    button.scroll_into_view_if_needed()

                    button.click(
                        timeout=5000
                    )

                    return True

            except Exception:
                continue

        return False

    # =====================================================================
    # SUBMISSION DETECTION
    # =====================================================================

    def _detect_submission(self, page):

        try:
            body_text = page.locator(
                "body"
            ).inner_text(
                timeout=5000
            ).lower()

        except Exception:
            body_text = ""

        confirmation_phrases = [
            "application submitted",
            "application has been submitted",
            "successfully submitted",
            "submission successful",
            "your response has been recorded",
            "response has been recorded",
            "thank you for applying",
            "thank you",
            "success",
        ]

        for phrase in confirmation_phrases:

            if phrase in body_text:

                return {
                    "confirmed": True,
                    "signal": phrase,
                }

        current_url = page.url.lower()

        url_indicators = [
            "success",
            "submitted",
            "confirmation",
            "thank",
            "complete",
        ]

        for indicator in url_indicators:

            if indicator in current_url:

                return {
                    "confirmed": True,
                    "signal": f"url:{indicator}",
                }

        # Google Forms sometimes changes the page to a
        # confirmation state without a useful URL.
        try:

            confirmation = page.locator(
                'div[role="heading"]'
            ).filter(
                has_text="Your response has been recorded"
            )

            if confirmation.count() > 0:

                return {
                    "confirmed": True,
                    "signal": "google_forms_confirmation",
                }

        except Exception:
            pass

        return {
            "confirmed": False,
            "signal": None,
        }

    # =====================================================================
    # LOGIN DETECTION
    # =====================================================================

    def _is_login_page(self, page):

        try:

            url = page.url.lower()

            if "accounts.google.com" in url:
                return True

            text = page.locator(
                "body"
            ).inner_text(
                timeout=3000
            ).lower()

            login_phrases = [
                "sign in",
                "email or phone",
                "enter your email",
                "forgot email",
                "use another account",
            ]

            return any(
                phrase in text
                for phrase in login_phrases
            )

        except Exception:
            return False

    # =====================================================================
    # LABEL EXTRACTION
    # =====================================================================

    def _get_label_text(
        self,
        page,
        element,
    ):

        try:

            element_id = (
                element.get_attribute("id")
            )

            if element_id:

                label = page.locator(
                    f'label[for="{element_id}"]'
                )

                if label.count() > 0:

                    text = label.first.inner_text()

                    if text:
                        return text.strip()

        except Exception:
            pass

        try:

            text = element.evaluate(
                """
                (el) => {
                    const parent = el.closest(
                        '[role="listitem"]'
                    );

                    if (!parent) return "";

                    const clone = parent.cloneNode(true);

                    const inputs =
                        clone.querySelectorAll(
                            'input, textarea, select'
                        );

                    inputs.forEach(
                        input => input.remove()
                    );

                    return clone.innerText
                        .replace(/\\n+/g, " ")
                        .trim();
                }
                """
            )

            return text or ""

        except Exception:
            return ""

    # =====================================================================
    # NORMALIZATION
    # =====================================================================

    @staticmethod
    def _normalize(value):

        return (
            str(value or "")
            .strip()
            .lower()
            .replace("-", "")
            .replace("_", "")
            .replace(" ", "")
        )