import hashlib


class SemanticCache:

    def __init__(self):

        self.cache = {}

    def generate_key(
        self,
        feature_name,
        commits
    ):

        combined_items = []

        for commit in commits:

            combined_items.append(
                "|".join(
                    [
                        str(commit.get("sha", "")),
                        str(commit.get("message", ""))
                    ]
                )
            )

        combined = (
            feature_name + "|" + "|".join(combined_items)
        )

        return hashlib.md5(
            combined.encode()
        ).hexdigest()

    def exists(
        self,
        cache_key
    ):

        return cache_key in self.cache

    def get(
        self,
        cache_key
    ):

        return self.cache.get(cache_key)

    def set(
        self,
        cache_key,
        value
    ):

        self.cache[cache_key] = value