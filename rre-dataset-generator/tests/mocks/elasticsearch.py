class MockRequest:
    def __init__(self, body="{}"):
        self.body = body

class MockResponseElasticsearchEngine:
    def __init__(self, json_data, url="", body="{}", status_code=200):
        self._json_data = json_data
        self.url = url
        self.status_code = status_code
        self.request = MockRequest(body)

    def json(self):
        return {
            "hits": {
                "hits": self._json_data if isinstance(self._json_data, list) else [self._json_data]
            }
        }
