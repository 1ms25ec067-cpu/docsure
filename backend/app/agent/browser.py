from typing import Any
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

from app.verification.store import evidence_store


class WebsiteApplicationAgent:
    def __init__(self):
        self.source = "docsure_browser_agent"

    def run(
        self,
        url: str,
        field_values: dict[str, str],
        submit: bool = True,
    ) -> dict[str, Any]:

        evidence = []

        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=[
                    "--no-proxy-server",
                    "--disable-blink-features=AutomationControlled",
                ],
            )

            context = browser.new_context(
                ignore_https_errors=True,
            )

            page = context.new_page()

            try:
                response = page.goto(
                    url,
                    wait_until="domcontentloaded",
                    timeout=30000,
                )

                page.wait_for_timeout(1000)

                evidence.append(
                    evidence_store.add(
                        source=self.source,
                        claim="Target application website was opened.",
                        value={
                            "url": page.url,
                            "title": page.title(),
                            "http_status": response.status if response else None,
                        },
                        verdict="VERIFIED",
                        evidence_type="WEBSITE_OPEN",
                        metadata={
                            "requested_url": url,
                        },
                    )
                )

                fields = self._discover_fields(page)

                evidence.append(
                    evidence_store.add(
                        source=self.source,
                        claim="Application form fields were inspected.",
                        value={
                            "field_count": len(fields),
                            "fields": fields,
                        },
                        verdict="VERIFIED",
                        evidence_type="FORM_DISCOVERY",
                        metadata={
                            "url": page.url,
                        },
                    )
                )

                mappings = []

                for source_field, value in field_values.items():
                    target = self._find_matching_field(
                        source_field,
                        fields,
                    )

                    if target is None:
                        evidence.append(
                            evidence_store.add(
                                source=self.source,
                                claim="Every required verified data field can be safely mapped to the website.",
                                value={
                                    "missing_field": source_field,
                                    "available_fields": fields,
                                },
                                verdict="BLOCKED",
                                evidence_type="FIELD_MAPPING",
                                metadata={
                                    "reason": "FIELD_NOT_FOUND",
                                },
                            )
                        )

                        return {
                            "status": "BLOCKED",
                            "reason": "FIELD_NOT_FOUND",
                            "url": url,
                            "field": source_field,
                            "available_fields": fields,
                            "evidence": evidence,
                        }

                    mappings.append(
                        {
                            "source_field": source_field,
                            "website_field": target["label"],
                            "value": value,
                        }
                    )

                evidence.append(
                    evidence_store.add(
                        source=self.source,
                        claim="Verified document data was mapped to website fields.",
                        value={
                            "mapping": mappings,
                        },
                        verdict="VERIFIED",
                        evidence_type="FIELD_MAPPING",
                        metadata={
                            "mapped_fields": len(mappings),
                        },
                    )
                )

                filled = []

                for source_field, value in field_values.items():
                    target = self._find_matching_field(
                        source_field,
                        fields,
                    )

                    try:
                        self._fill_field(page, target, value)

                        filled.append(
                            {
                                "source_field": source_field,
                                "website_field": target["label"],
                                "value": value,
                            }
                        )

                    except Exception as error:
                        evidence.append(
                            evidence_store.add(
                                source=self.source,
                                claim="Mapped application fields were filled.",
                                value={
                                    "field": source_field,
                                    "error": str(error),
                                },
                                verdict="BLOCKED",
                                evidence_type="FORM_FILLING",
                                metadata={
                                    "reason": "FIELD_FILL_FAILED",
                                },
                            )
                        )

                        return {
                            "status": "BLOCKED",
                            "reason": "FIELD_FILL_FAILED",
                            "field": source_field,
                            "error": str(error),
                            "evidence": evidence,
                        }

                evidence.append(
                    evidence_store.add(
                        source=self.source,
                        claim="Mapped application fields were filled.",
                        value={
                            "filled_count": len(filled),
                            "fields": filled,
                        },
                        verdict="VERIFIED",
                        evidence_type="FORM_FILLING",
                        metadata={
                            "field_count": len(filled),
                        },
                    )
                )

                verification = []

                for source_field, expected in field_values.items():
                    target = self._find_matching_field(
                        source_field,
                        fields,
                    )

                    actual = self._read_field(
                        page,
                        target,
                    )

                    verified = str(actual).strip() == str(expected).strip()

                    verification.append(
                        {
                            "field": target["label"],
                            "expected": expected,
                            "actual": actual,
                            "verified": verified,
                        }
                    )

                    if not verified:
                        evidence.append(
                            evidence_store.add(
                                source=self.source,
                                claim="All entered values were independently read back and verified.",
                                value={
                                    "verification": "FORM_VALUES_NOT_CONFIRMED",
                                    "fields": verification,
                                },
                                verdict="BLOCKED",
                                evidence_type="FORM_VALUE_VERIFICATION",
                                metadata={
                                    "reason": "VALUE_MISMATCH",
                                },
                            )
                        )

                        return {
                            "status": "BLOCKED",
                            "reason": "FORM_VALUES_NOT_CONFIRMED",
                            "verification": verification,
                            "evidence": evidence,
                        }

                evidence.append(
                    evidence_store.add(
                        source=self.source,
                        claim="All entered values were independently read back and verified.",
                        value={
                            "verification": "FORM_VALUES_CONFIRMED",
                            "fields": verification,
                        },
                        verdict="VERIFIED",
                        evidence_type="FORM_VALUE_VERIFICATION",
                        metadata={
                            "verified_fields": len(verification),
                        },
                    )
                )

                if not submit:
                    return {
                        "status": "VERIFIED",
                        "reason": "FORM_FILLED_AND_VERIFIED",
                        "url": url,
                        "verification": verification,
                        "evidence": evidence,
                    }

                self._submit(page)

                page.wait_for_load_state(
                    "domcontentloaded",
                    timeout=10000,
                )

                page.wait_for_timeout(1000)

                confirmation = self._detect_submission(page)

                if confirmation["confirmed"]:
                    submission_evidence = evidence_store.add(
                        source=self.source,
                        claim="Application reached a confirmed submitted state.",
                        value={
                            "verification": "SUBMISSION_CONFIRMED",
                            "final_url": page.url,
                            "confirmation_text": confirmation["text"],
                        },
                        verdict="VERIFIED",
                        evidence_type="SUBMISSION_VERIFICATION",
                        metadata={
                            "reason": "CONFIRMATION_DETECTED",
                        },
                    )

                    evidence.append(submission_evidence)

                    return {
                        "status": "VERIFIED",
                        "reason": "APPLICATION_SUBMITTED_AND_VERIFIED",
                        "final_url": page.url,
                        "verification": verification,
                        "submission": confirmation,
                        "evidence": evidence,
                    }

                evidence.append(
                    evidence_store.add(
                        source=self.source,
                        claim="Application reached a confirmed submitted state.",
                        value={
                            "verification": "SUBMISSION_NOT_CONFIRMED",
                            "final_url": page.url,
                        },
                        verdict="BLOCKED",
                        evidence_type="SUBMISSION_VERIFICATION",
                        metadata={
                            "reason": "UNKNOWN_SUBMISSION_STATE",
                        },
                    )
                )

                return {
                    "status": "BLOCKED",
                    "reason": "SUBMISSION_NOT_CONFIRMED",
                    "final_url": page.url,
                    "verification": verification,
                    "evidence": evidence,
                }

            except PlaywrightTimeoutError as error:
                evidence.append(
                    evidence_store.add(
                        source=self.source,
                        claim="Website automation completed without a browser timeout.",
                        value={
                            "url": url,
                            "error": str(error),
                        },
                        verdict="BLOCKED",
                        evidence_type="BROWSER_ERROR",
                        metadata={
                            "reason": "TIMEOUT",
                        },
                    )
                )

                return {
                    "status": "BLOCKED",
                    "reason": "BROWSER_TIMEOUT",
                    "error": str(error),
                    "evidence": evidence,
                }

            finally:
                context.close()
                browser.close()

    def _discover_fields(self, page):
        fields = []

        elements = page.locator(
            "input, textarea, select"
        )

        count = elements.count()

        for index in range(count):
            element = elements.nth(index)

            try:
                if not element.is_visible():
                    continue

                tag = element.evaluate(
                    "(el) => el.tagName.toLowerCase()"
                )

                field_type = element.get_attribute("type") or tag
                name = element.get_attribute("name") or ""
                placeholder = element.get_attribute("placeholder") or ""
                aria = element.get_attribute("aria-label") or ""
                element_id = element.get_attribute("id") or ""

                label = (
                    name
                    or placeholder
                    or aria
                    or element_id
                )

                if element_id:
                    associated = page.locator(
                        f'label[for="{element_id}"]'
                    )

                    if associated.count() > 0:
                        label_text = associated.first.inner_text().strip()

                        if label_text:
                            label = label_text

                fields.append(
                    {
                        "label": label,
                        "type": field_type,
                        "name": name,
                        "id": element_id,
                        "placeholder": placeholder,
                        "aria_label": aria,
                    }
                )

            except Exception:
                continue

        return fields

    def _find_matching_field(self, source_field, fields):
        source = str(source_field).strip().lower()

        # Exact match
        for field in fields:
            candidates = [
                field.get("label", ""),
                field.get("name", ""),
                field.get("id", ""),
                field.get("placeholder", ""),
                field.get("aria_label", ""),
            ]

            for candidate in candidates:
                if str(candidate).strip().lower() == source:
                    return field

        # Partial match
        for field in fields:
            candidates = [
                field.get("label", ""),
                field.get("name", ""),
                field.get("id", ""),
                field.get("placeholder", ""),
                field.get("aria_label", ""),
            ]

            for candidate in candidates:
                candidate = str(candidate).strip().lower()

                if source in candidate or candidate in source:
                    return field

        return None

    def _get_locator(self, page, field):
        element_id = field.get("id")
        name = field.get("name")
        label = field.get("label")
        placeholder = field.get("placeholder")

        if element_id:
            locator = page.locator(
                f"#{element_id}"
            )

            if locator.count() > 0:
                return locator.first

        if name:
            locator = page.locator(
                f'[name="{name}"]'
            )

            if locator.count() > 0:
                return locator.first

        if placeholder:
            locator = page.get_by_placeholder(
                placeholder,
                exact=True,
            )

            if locator.count() > 0:
                return locator.first

        if label:
            locator = page.get_by_label(
                label,
                exact=False,
            )

            if locator.count() > 0:
                return locator.first

        raise ValueError(
            f"Could not locate field: {field}"
        )

    def _fill_field(self, page, field, value):
        locator = self._get_locator(page, field)

        field_type = field.get("type", "").lower()

        if field_type in {
            "radio",
            "checkbox",
        }:
            locator.check()
        else:
            locator.fill(str(value))

    def _read_field(self, page, field):
        locator = self._get_locator(page, field)

        field_type = field.get("type", "").lower()

        if field_type in {
            "radio",
            "checkbox",
        }:
            return str(locator.is_checked())

        return locator.input_value()

    def _submit(self, page):
        selectors = [
            'button[type="submit"]',
            'input[type="submit"]',
            'button:has-text("Submit Application")',
            'button:has-text("Submit")',
            'button:has-text("Apply")',
            'button:has-text("Continue")',
            'button:has-text("Finish")',
            '[role="button"]:has-text("Submit")',
        ]

        for selector in selectors:
            locator = page.locator(selector)

            if locator.count() > 0:
                visible = locator.filter(
                    has_not=page.locator("[hidden]")
                )

                if visible.count() > 0:
                    visible.first.click()
                    return

                locator.first.click()
                return

        raise ValueError(
            "No supported submit button was found."
        )

    def _detect_submission(self, page):
        body_text = page.locator("body").inner_text().lower()

        confirmation_phrases = [
            "application submitted successfully",
            "application has been submitted",
            "application submitted",
            "successfully submitted",
            "submission successful",
            "submission confirmed",
            "your application has been submitted",
            "thank you for applying",
            "response has been recorded",
        ]

        for phrase in confirmation_phrases:
            if phrase in body_text:
                return {
                    "confirmed": True,
                    "text": phrase,
                }

        url = page.url.lower()

        url_indicators = [
            "success",
            "submitted",
            "confirmation",
            "complete",
            "thank",
        ]

        if any(indicator in url for indicator in url_indicators):
            return {
                "confirmed": True,
                "text": f"Confirmation URL: {page.url}",
            }

        return {
            "confirmed": False,
            "text": "",
        }