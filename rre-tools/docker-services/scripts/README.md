## Extract BBC News Dataset 

[The script](extract_bbc_news_dataset.py) downloads and processes BBC News articles from the [RealTimeData/bbc_news_alltime](https://huggingface.co/datasets/RealTimeData/bbc_news_alltime)
dataset using HuggingFace.

It filters, deduplicates, truncates long content, adds UUIDs, and saves the results to a JSON file.

```
python extract_bbc_news_dataset.py --filename output.json
```
Arguments:

`--filename`: Output JSON filename (default: dataset.json)
