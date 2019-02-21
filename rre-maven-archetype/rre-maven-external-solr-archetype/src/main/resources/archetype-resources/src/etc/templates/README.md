This folder will contain the query templates associated with the evaluation suite. 
A template is a JSON file containing a JSON object with name->value(s) pairs corresponding to query parameters. 
Although it is completely ok to have statically-defined values here, usually you will be using placeholders.

```javascript
  {
    "q": "$query",
    "fq": "language:$lang"
  }
```
The placeholders values will be defined within the ratings file, specifically in the queries definitions. 