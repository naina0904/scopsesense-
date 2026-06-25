from backend.core.project_context import (
    UnifiedProjectContext
)


class ContextBuilder:

    def __init__(self):

        self.context = (
            UnifiedProjectContext()
        )

    def merge(
        self,
        normalized_data
    ):

        for key, value in (
            normalized_data.items()
        ):

            if hasattr(
                self.context,
                key
            ):

                current = getattr(
                    self.context,
                    key
                )

                if isinstance(
                    current,
                    list
                ):

                    current.extend(value)

        return self.context