class MockRequest:
    def __init__(self, body="{}"):
        self.body = body

class MockResponseSolrEngine:
    def __init__(self, json_data, url="", body="{}", status_code=200):
        self._json_data = json_data
        self.url = url
        self.status_code = status_code
        self.request = MockRequest(body)

    def json(self):
        return {
            "response": {
                "docs": self._json_data if isinstance(self._json_data, list) else [self._json_data]
            }
        }

class MockResponseUniqueKey:
    def __init__(self, ident):
        self._id = ident

    def json(self):
        return {
            "responseHeader":
                {
                    "status":0,
                    "QTime":2
                },
            "uniqueKey": self._id
        }
