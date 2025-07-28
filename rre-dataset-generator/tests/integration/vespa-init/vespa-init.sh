#!/usr/bin/env bash
set -euo pipefail

docker exec -it vespa bash -c "vespa deploy --wait 300 ./app"
# EXPECTED:
# Waiting up to 5m0s for deployment to converge...
docker exec -it vespa bash -c "sleep 5"


docker exec -it vespa bash -c "vespa feed dataset/*.json"
# EXPECTED:
# {
#   "feeder.operation.count": 1,
#   "feeder.seconds": 0.332,
#   "feeder.ok.count": 1,
#   "feeder.ok.rate": 1.000,
#   "feeder.error.count": 0,
#   "feeder.inflight.count": 0,
#   "http.request.count": 1,
#   "http.request.bytes": 303,
#   "http.request.MBps": 0.000,
#   "http.exception.count": 0,
#   "http.response.count": 1,
#   "http.response.bytes": 66,
#   "http.response.MBps": 0.000,
#   "http.response.error.count": 0,
#   "http.response.latency.millis.min": 330,
#   "http.response.latency.millis.avg": 330,
#   "http.response.latency.millis.max": 330,
#   "http.response.code.counts": {
#     "200": 1
#   }
# }

docker exec -it vespa bash -c "sleep 5"


docker exec -it vespa bash -c "vespa query \"select * from news where true\" language=en-US"
# EXPECTED:
# {
#     "root": {
#         "id": "toplevel",
#         "relevance": 1.0,
#         "fields": {
#             "totalCount": 1
#         },
#         "coverage": {
#             "coverage": 100,
#             "documents": 1,
#             "full": true,
#             "nodes": 1,
#             "results": 1,
#             "resultsFull": 1
#         },
#         "children": [
#             {
#                 "id": "id:news:news::1",
#                 "relevance": 0.0,
#                 "source": "news",
#                 "fields": {
#                     "sddocname": "news",
#                     "documentid": "id:news:news::1",
#                     "id": "1",
#                     "title": "Helicopter Crashes in Colombian Drug War, Kills 20",
#                     "description": "BOGOTA, Colombia  - A U.S.-made helicopter on an anti-drugs mission crashed in the Colombian jungle on Thursday, killing all 20 Colombian soldiers aboard, the army said."
#                 }
#             }
#         ]
#     }
# }