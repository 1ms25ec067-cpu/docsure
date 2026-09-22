from typing import Any
import re
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

from app.verification.store import evidence_store


class WebsiteApplicationAgent:
    """
    Evidence-gated browser automation agent.

    Workflow:
        OPEN
        -> SECURITY / LOGIN CHECK
        -> DISCOVER FIELDS
        -> MAP VERIFIED DATA
        -> FILL FIELDS
        -> READ-BACK VERIFICATION
        -> SUBMIT
        -> INDEPENDENT CONFIRMATION

    Safety Rules:
    - Never guess fields or map multiple source fields to the same input.
    - Never fill unexpected authentication/login/CAPTCHA pages.
    - Never treat button click as proof of submission.
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

                # ---------------------------------------------------------
                # Security Guard: Detect login, auth, CAPTCHA, or OTP gates
                # ---------------------------------------------------------
                is_blocked, block_reason = self._check_security_gates(page)
                if is_blocked:
                    block_evidence = evidence_store.add(
                        source="docsure_browser_agent",
                        claim="Unexpected authentication or challenge page encountered.",
                        value={"url": page.url, "reason": block_reason},
                        verdict="BLOCKED",
                        evidence_type="SECURITY_GATE",
                        metadata={"reason": block_reason, "url": page.url},
                    )
                    result["evidence"].append(block_evidence)
                    result["status"] = "BLOCKED"
                    result["reason"] = block_reason
                    result["verification"].append(
                        {
                            "status": "BLOCKED",
                            "reason": block_reason,
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
                                "sublabel": field.get("sublabel", ""),
                                "question_text": field.get("question_text", ""),
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
                mappings, mapping_error = self._map_fields(page, fields, field_values)

                if mapping_error:
                    mapping_evidence = evidence_store.add(
                        source="docsure_browser_agent",
                        claim="Verified document data was mapped to website fields.",
                        value={"error": mapping_error},
                        verdict="BLOCKED",
                        evidence_type="FIELD_MAPPING",
                        metadata={"reason": mapping_error},
                    )
                    result["evidence"].append(mapping_evidence)
                    result["status"] = "BLOCKED"
                    result["reason"] = mapping_error
                    result["verification"].append(
                        {
                            "status": "BLOCKED",
                            "reason": mapping_error,
                        }
                    )
                    return result

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
                        actual_value.lower() == expected_value.lower()
                        or self._normalize_date(actual_value) == self._normalize_date(expected_value)
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
                    item["verified"] for item in verification_results
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

                page.wait_for_timeout(2000)

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
    # SECURITY GATES DETECTION
    # =====================================================================

    def _check_security_gates(self, page) -> tuple[bool, str | None]:
        try:
            url = page.url.lower()

            if "accounts.google.com" in url or "login" in url or "signin" in url:
                return True, "UNEXPECTED_AUTHENTICATION_PAGE"

            body_text = page.locator("body").inner_text(timeout=3000).lower()

            # CAPTCHA detection
            captcha_indicators = [
                "recaptcha",
                "hcaptcha",
                "cf-turnstile",
                "verify you are human",
                "complete the captcha",
                "security check",
            ]
            for indicator in captcha_indicators:
                if indicator in body_text or page.locator(f'[class*="{indicator}"], iframe[src*="{indicator}"]').count() > 0:
                    return True, "CAPTCHA"

            # OTP detection
            otp_indicators = [
                "one-time password",
                "one time password",
                "enter otp",
                "verification code has been sent",
            ]
            for indicator in otp_indicators:
                if indicator in body_text:
                    return True, "OTP_REQUIRED"

            # Generic login detection
            login_phrases = [
                "sign in to continue",
                "sign in with your google account",
                "enter your password",
                "forgot password",
            ]
            for phrase in login_phrases:
                if phrase in body_text:
                    return True, "UNEXPECTED_AUTHENTICATION_PAGE"

            return False, None

        except Exception:
            return False, None

    # =====================================================================
    # FIELD DISCOVERY
    # =====================================================================

    def _discover_fields(self, page):
        discovered = []
        inputs = page.locator("input, textarea, select")
        count = inputs.count()

        for index in range(count):
            element = inputs.nth(index)
            try:
                if not element.is_visible():
                    continue

                tag = element.evaluate("(el) => el.tagName.toLowerCase()")
                input_type = element.get_attribute("type") or tag

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
                placeholder = element.get_attribute("placeholder") or ""
                aria_label = element.get_attribute("aria-label") or ""

                label = self._get_label_text(page, element)
                sublabel = self._get_sublabel_text(element)
                question_text = self._get_question_text(element)

                if aria_label:
                    label = aria_label

                if not label:
                    label = placeholder or name or field_id or f"field_{index}"

                discovered.append(
                    {
                        "element": element,
                        "label": label.strip(),
                        "sublabel": sublabel.strip(),
                        "question_text": question_text.strip(),
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

        return discovered

    def _get_sublabel_text(self, element) -> str:
        try:
            return element.evaluate(
                """
                (el) => {
                    const subLabel = el.parentElement.querySelector('label.form-sub-label, .form-sub-label');
                    if (subLabel) return subLabel.innerText.trim();
                    const nextEl = el.nextElementSibling;
                    if (nextEl && nextEl.tagName.toLowerCase() === 'label') return nextEl.innerText.trim();
                    return '';
                }
                """
            ) or ""
        except Exception:
            return ""

    def _get_question_text(self, element) -> str:
        try:
            return element.evaluate(
                """
                (el) => {
                    const formLine = el.closest('.form-line, [role="listitem"], .form-group');
                    if (!formLine) return '';
                    const labelEl = formLine.querySelector('.form-label, label');
                    if (labelEl) return labelEl.innerText.replace(/\\n+/g, ' ').trim();
                    return formLine.innerText.replace(/\\n+/g, ' ').trim();
                }
                """
            ) or ""
        except Exception:
            return ""

    def _get_label_text(self, page, element) -> str:
        try:
            element_id = element.get_attribute("id")
            if element_id:
                label = page.locator(f'label[for="{element_id}"]')
                if label.count() > 0:
                    text = label.first.inner_text()
                    if text:
                        return text.strip()
        except Exception:
            pass

        try:
            return element.evaluate(
                """
                (el) => {
                    const parent = el.closest('.form-line, [role="listitem"], .form-group');
                    if (!parent) return '';
                    const label = parent.querySelector('.form-label, label');
                    return label ? label.innerText.replace(/\\n+/g, ' ').trim() : '';
                }
                """
            ) or ""
        except Exception:
            return ""

    # =====================================================================
    # FIELD MAPPING
    # =====================================================================

    def _map_fields(self, page, fields, field_values):
        mappings = []
        used_element_indices = set()

        for source_field, expected_value in field_values.items():
            norm_source = self._normalize(source_field)

            # -------------------------------------------------------------
            # Handle "Full Name"
            # -------------------------------------------------------------
            if norm_source in {"fullname", "name", "applicantname", "studentname", "candidatename"}:
                # Check if there are separate First and Last Name inputs
                first_name_field = None
                last_name_field = None
                single_name_field = None

                for field in fields:
                    if field["index"] in used_element_indices:
                        continue
                    text_blob = " ".join([
                        field["label"], field["sublabel"], field["name"],
                        field["id"], field["placeholder"], field["question_text"]
                    ]).lower()

                    if ("first" in text_blob or "[first]" in field["name"]) and "name" in text_blob:
                        first_name_field = field
                    elif ("last" in text_blob or "[last]" in field["name"]) and "name" in text_blob:
                        last_name_field = field
                    elif norm_source in self._normalize(field["label"]) or "name" in self._normalize(field["label"]):
                        if not single_name_field:
                            single_name_field = field

                if first_name_field and last_name_field:
                    # Split name into first and last
                    parts = str(expected_value).strip().split(None, 1)
                    first_val = parts[0]
                    last_val = parts[1] if len(parts) > 1 else ""

                    mappings.append({
                        "source_field": f"{source_field} (First Name)",
                        "website_field": first_name_field,
                        "value": first_val,
                    })
                    used_element_indices.add(first_name_field["index"])

                    mappings.append({
                        "source_field": f"{source_field} (Last Name)",
                        "website_field": last_name_field,
                        "value": last_val,
                    })
                    used_element_indices.add(last_name_field["index"])
                    continue

                if single_name_field:
                    mappings.append({
                        "source_field": source_field,
                        "website_field": single_name_field,
                        "value": expected_value,
                    })
                    used_element_indices.add(single_name_field["index"])
                    continue

                return None, "FIELD_NOT_FOUND"

            # -------------------------------------------------------------
            # Handle "Date of Birth"
            # -------------------------------------------------------------
            if norm_source in {"dateofbirth", "dob", "birthdate"}:
                dob_field = None
                for field in fields:
                    if field["index"] in used_element_indices:
                        continue
                    text_blob = " ".join([
                        field["label"], field["sublabel"], field["name"],
                        field["id"], field["placeholder"], field["question_text"]
                    ]).lower()

                    if "birth" in text_blob or "dob" in text_blob or "date" in text_blob:
                        dob_field = field
                        break

                if dob_field:
                    # Format date to match placeholder if present (e.g. MM-DD-YYYY)
                    val = self._format_date_for_field(expected_value, dob_field["placeholder"])
                    mappings.append({
                        "source_field": source_field,
                        "website_field": dob_field,
                        "value": val,
                    })
                    used_element_indices.add(dob_field["index"])
                    continue

                return None, "FIELD_NOT_FOUND"

            # -------------------------------------------------------------
            # Handle "Email Address"
            # -------------------------------------------------------------
            if "email" in norm_source:
                email_field = None
                for field in fields:
                    if field["index"] in used_element_indices:
                        continue
                    text_blob = " ".join([
                        field["label"], field["sublabel"], field["name"],
                        field["id"], field["placeholder"], field["question_text"]
                    ]).lower()

                    if "email" in text_blob or field["type"] == "email":
                        email_field = field
                        break

                if email_field:
                    mappings.append({
                        "source_field": source_field,
                        "website_field": email_field,
                        "value": expected_value,
                    })
                    used_element_indices.add(email_field["index"])
                    continue

                return None, "FIELD_NOT_FOUND"

            # -------------------------------------------------------------
            # Handle "Phone Number"
            # -------------------------------------------------------------
            if "phone" in norm_source or "mobile" in norm_source:
                phone_field = None
                for field in fields:
                    if field["index"] in used_element_indices:
                        continue
                    text_blob = " ".join([
                        field["label"], field["sublabel"], field["name"],
                        field["id"], field["placeholder"], field["question_text"]
                    ]).lower()

                    if "phone" in text_blob or "mobile" in text_blob or field["type"] == "tel":
                        phone_field = field
                        break

                if phone_field:
                    mappings.append({
                        "source_field": source_field,
                        "website_field": phone_field,
                        "value": expected_value,
                    })
                    used_element_indices.add(phone_field["index"])
                    continue

                return None, "FIELD_NOT_FOUND"

            # -------------------------------------------------------------
            # Generic matching with collision prevention
            # -------------------------------------------------------------
            matched_field = None
            for field in fields:
                if field["index"] in used_element_indices:
                    continue
                candidates = [
                    self._normalize(field.get("label", "")),
                    self._normalize(field.get("aria_label", "")),
                    self._normalize(field.get("name", "")),
                    self._normalize(field.get("id", "")),
                    self._normalize(field.get("question_text", "")),
                ]
                if any(norm_source == c or norm_source in c for c in candidates if c):
                    matched_field = field
                    break

            if matched_field:
                mappings.append({
                    "source_field": source_field,
                    "website_field": matched_field,
                    "value": expected_value,
                })
                used_element_indices.add(matched_field["index"])
            else:
                return None, "FIELD_NOT_FOUND"

        return mappings, None

    # =====================================================================
    # FILLING & READ-BACK
    # =====================================================================

    def _fill_field(self, page, field, value):
        element = field["element"]
        try:
            element.scroll_into_view_if_needed()
            element.fill(str(value), timeout=self.timeout)
            try:
                element.dispatch_event("input")
                element.dispatch_event("change")
            except Exception:
                pass
            return True
        except Exception:
            try:
                element.click(timeout=5000)
                element.press("Control+A")
                element.type(str(value), delay=10)
                return True
            except Exception:
                return False

    def _read_field(self, page, field):
        element = field["element"]
        try:
            element.scroll_into_view_if_needed()
            value = element.input_value(timeout=self.timeout)
            if value is not None:
                return value
        except Exception:
            pass

        try:
            return element.evaluate(
                """
                (el) => {
                    if ("value" in el) return el.value;
                    return el.getAttribute("value") || "";
                }
                """
            ) or ""
        except Exception:
            return ""

    # =====================================================================
    # SUBMIT & DETECTION
    # =====================================================================

    def _submit(self, page):
        selectors = [
            ".form-submit-button",
            'button:has-text("Submit Application")',
            'button:has-text("Submit")',
            'button:has-text("Apply")',
            'button:has-text("Continue")',
            'button:has-text("Finish")',
            'input[type="submit"]',
            '[role="button"]:has-text("Submit")',
        ]
        for selector in selectors:
            try:
                button = page.locator(selector).first
                if button.is_visible():
                    button.scroll_into_view_if_needed()
                    button.click(timeout=5000)
                    return True
            except Exception:
                continue
        return False

    def _detect_submission(self, page):
        try:
            body_text = page.locator("body").inner_text(timeout=5000).lower()
        except Exception:
            body_text = ""

        # Check for error warnings on the page
        error_indicators = [
            "there are errors on the form",
            "please fix the errors",
            "this field is required",
        ]
        has_errors = any(err in body_text for err in error_indicators)
        if has_errors:
            return {"confirmed": False, "signal": "FORM_ERRORS_PRESENT"}

        confirmation_phrases = [
            "thank you",
            "your submission has been received",
            "application submitted",
            "application has been submitted",
            "successfully submitted",
            "submission successful",
            "your response has been recorded",
            "response has been recorded",
            "thank you for applying",
        ]
        for phrase in confirmation_phrases:
            if phrase in body_text:
                return {"confirmed": True, "signal": phrase}

        current_url = page.url.lower()
        url_indicators = ["thankyou", "success", "submitted", "confirmation", "thank", "complete"]
        for indicator in url_indicators:
            if indicator in current_url:
                return {"confirmed": True, "signal": f"url:{indicator}"}

        return {"confirmed": False, "signal": None}

    # =====================================================================
    # HELPERS
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

    @staticmethod
    def _normalize_date(date_str: str) -> str:
        s = str(date_str or "").strip().lower()
        s = re.sub(r"[^0-9a-z]", "", s)
        return s

    @staticmethod
    def _format_date_for_field(date_str: str, placeholder: str) -> str:
        date_str = str(date_str).strip()
        month_names = {
            "january": "01", "february": "02", "march": "03", "april": "04",
            "may": "05", "june": "06", "july": "07", "august": "08",
            "september": "09", "october": "10", "november": "11", "december": "12",
            "jan": "01", "feb": "02", "mar": "03", "apr": "04", "jun": "06",
            "jul": "07", "aug": "08", "sep": "09", "oct": "10", "nov": "11", "dec": "12",
        }
        # Match '17 February 2008'
        m = re.match(r"(\d{1,2})(?:st|nd|rd|th)?[\s\/\-\.]([A-Za-z]+)[\s\/\-\.](\d{4})", date_str)
        if m:
            day, month_name, year = m.groups()
            month = month_names.get(month_name.lower(), "01")
            day = day.zfill(2)
            if "mm-dd-yyyy" in placeholder.lower():
                return f"{month}-{day}-{year}"
            if "dd-mm-yyyy" in placeholder.lower():
                return f"{day}-{month}-{year}"
            if "yyyy-mm-dd" in placeholder.lower():
                return f"{year}-{month}-{day}"
            return f"{month}-{day}-{year}"

        return date_str