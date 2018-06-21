This folder will contain the query templates associated with the evaluation suite. 
The query shape in Elasticsearch is already a JSON file so each template should be a valid Elasticsearch query 
with all needed placeholders (that will be defined within the ratings file).

```javascript
{
  "size": 0,
  "query": {
    "bool": {
      "must": [
        {
          "multi_match": {
            "query": "$query",
            "fields": [
              "some_searchable_field_1^1.75",
              "some_other_searchable_field"
            ],
            "minimum_should_match": "3<-45% 6<-95%"
          }
        }
      ]
    }
  },
  "aggs": {
    "headings": {
      "terms": {
        "field": "title_sugg",
        "order": { "max_score": "desc" }
      },
      "aggs": {
        "max_score": {
          "max": {
            "script": {
              "lang": "painless",
              "inline": "_score"
            }
          }
        }
      }
    }
  }
}
```