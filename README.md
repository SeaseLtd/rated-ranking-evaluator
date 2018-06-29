# Rated Ranking Evaluator

The Rated Ranking Evaluator (RRE) is a search quality evaluation tool which, as the name suggests, evaluates the quality of results coming from a search infrastructure. 

For a detailed description of the project, please visit

* The project Wiki, located at https://github.com/SeaseLtd/rated-ranking-evaluator/wiki   
* Our talk about RRE at the Apache Lucene/Solr London meetup: https://www.slideshare.net/AndreaGazzarini/search-quality-evaluation-a-developer-perspective   

At the moment Apache Solr and Elasticsearch are supported (see the documentation for supported versions). 

RRE is a multi-module project which consists of:

* **a core**, that is the central library which is in charge to produce the evaluation results
* a **search-platform API**: for abstracting (and binding) the underlying search platform
* a set of **search-platform bindings**: as said above, at the moment we have two available bindings (Apache Solr and Elasticsearch)
* an **Apache Maven plugin** for each available search platform binding: which allows to inject RRE into a Maven-based build system
* an **Apache Maven reporting plugin**: for producing evaluation reports in a human-readable format (e.g. PDF, excel), useful for targeting non-technical users 
* an **RRE Server**: a simple web-based control panel where evaluation results are updated in realtime after each build cycle. 

![RRE Console](https://user-images.githubusercontent.com/7569632/41497947-0c09516e-7161-11e8-8684-13dfc75ef4ba.png)

The whole system has been built as a framework where metrics can be configured/activated and even plugged-in (of course, this option requires some development)
The metrics that are part of the current RRE release are: 

* **Precision**: the fraction of retrieved documents that are relevant
* **Recall**: the fraction of relevant documents that are retrieved
* **Precision at 1**: this metric indicates if the first top result in the list is relevant or not.
* **Precision at 2**: same as above but it consider the first two results. 
* **Precision at 3**: same as above but it consider the first three results. 
* **Precision at 10**: this metric measures the number of relevant results in the top 10 search results
* **Reciprocal Rank**: it is the multiplicative inverse of the rank of the first "correct" answer: 1 for first place, 1/2 for second place, 1/3 for third and so on. 
* **Average Precision**: the area under the precision-recall curve.
* **NDCG at 10**: it is the multiplicative inverse of the rank of the first "correct" answer: 1 for first place, 1/2 for second place, 1/3 for third and so on. 

On top of those "leaf" metrics, which are computed at query level, RRE provides a rich nested data model, where the same metric can be aggregated at several levels.
For example, queries are grouped in Query Groups and Query Groups are grouped in Topics. 
That means the same metrics listed above are also available at upper levels using the arithmentic mean as aggregation criteria. 
As consequence of that RRE provides also the following metrics:  

* **Mean Average Precision**: the mean of the average precisions computed at query level. 
* **Mean Reciprocal Rank**: the average of the reciprocal ranks computed at query level.
* **all other metrics listed above** aggregared by their arithmetic mean

One the most important things you can see in the screenshot above is that RRE is able to keep track (and to make comparisons) between several versions of the system under evaluation. 

It encourages an incremental/iterative/immutable approach when developing and evolving a search system: assuming you're starting from version 1.0, when you apply some relevant change to your configuration, 
instead of changing that version, is better to clone it and apply the changes to the new version (let's call it 1.1). 

In this way, when the system build happens, RRE will compute everything explained above (i.e. the metrics) for each available version.   

In addition, it will provide the delta/trend between subsequent versions, so you can immediately get the overall direction where the system is going, in terms of relevance improvements. 

![delta](https://user-images.githubusercontent.com/7569632/41497997-5e9d2c4c-7162-11e8-9304-d8f529b6a9eb.png)
