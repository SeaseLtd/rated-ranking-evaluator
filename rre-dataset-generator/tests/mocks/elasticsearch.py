class MockResponseElasticsearchEngine:
    def __init__(self, json_data, status_code=200):
        self._json_data = json_data
        self.status_code = status_code

    def json(self):
        return {
            "hits": {
                "hits": self._json_data if isinstance(self._json_data, list) else [self._json_data]
            }
        }
