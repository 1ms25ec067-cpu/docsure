class FormFiller:

    async def fill(
        self,
        page,
        data: dict,
    ):
        results = []

        for field_name, expected_value in data.items():

            locator = page.locator(
                f'[name="{field_name}"]'
            )

            count = await locator.count()

            if count == 0:
                results.append({
                    "field": field_name,
                    "status": "NOT_FOUND",
                })
                continue

            field = locator.first

            await field.fill(
                str(expected_value)
            )

            actual_value = (
                await field.input_value()
            )

            verified = (
                actual_value
                == str(expected_value)
            )

            results.append({
                "field": field_name,
                "expected": str(expected_value),
                "actual": actual_value,
                "status": (
                    "VERIFIED"
                    if verified
                    else "FAILED"
                ),
            })

        return results