from typing import Optional

from playwright.async_api import Page


class ScholarEasePortal:

    def __init__(
        self,
        page: Page,
    ):
        self.page = page

    async def open(
        self,
        url: str,
    ):
        await self.page.goto(
            url,
            wait_until="domcontentloaded",
        )

        return {
            "status": "PAGE_OPENED",
            "url": self.page.url,
        }

    async def get_status(self):
        return {
            "status": "UNVERIFIED",
            "reason": "Portal status observer not configured",
        }

    async def get_application_id(
        self,
    ) -> Optional[str]:
        return None