### **UPDATE: RRE Local Setup & First Evaluation Run**

***Goal***: understand how RRE works, how to configure and run it locally with Elasticsearch, and how to correctly provide relevance judgements in the required format (`<query, document ID, gain>`).

---

### **Steps Performed**

1. **Clone and build RRE core project**

   ```bash
   cd rated-ranking-evaluator/
   mvn clean install
   ```

2. **Create a custom evaluation module**

   ```bash
   mkdir my-rre-evaluation/
   ```

3. **Run Elasticsearch locally (on port `9200`)**

4. **Craft a minimal test dataset**

   ```
   my-rre-evaluation/src/etc/
   ├── corpora/
   │   ├── doc1.json
   │   └── doc2.json
   ├── templates/
   │   └── match_query.json
   └── ratings.json
   ```

5. **Create `pom.xml` in `my-rre-evaluation/`**
   Configured with `rre-maven-external-elasticsearch-plugin` pointing to `src/etc`.

6. **Run the evaluation**

   ```bash
   mvn rre:evaluate
   ```

7. **Inspect results**
   Output written to:

   ```
   target/rre/evaluation.json
   ```

---

### **Current Outcome**

* OK: Pipeline executes end-to-end without errors.
* KO: **All metrics currently return 0 (e.g. Precision\@1, @3, @10).**

  After debugging:

  * `ratings.json` initially included:

    * Invalid comments (JSON does not support comments).
    * Missing `"index"` at the root.
    * Missing `"query_placeholder"` (required to map templates with query text).
  * These issues were fixed. But.. 🟡 **Remaining issue**: current Elasticsearch query returns no matching results, (empty index) -  likely due to mismatch between the template and document fields.

---

### **Key Learnings & Clarifications**

#### **Required Fields in Documents**

* `id` → Must match `id_field` declared in `ratings.json`.
* `body` (or another field) → Must match the field used in the query template.

In our case, the template was:

```json
"match": { "body": "${query}" }
```

→ Documents must contain a `"body"` field with searchable text.

#### **Can gain be multi-graded?**

Yes. The `gain` field supports integer values (e.g. 0, 1, 2..) and is used by metrics like **nDCG**. Binary relevance is supported, but multi-graded values are preferred for more informative evaluations.

#### **Is `rre-server` required?**

No. All evaluation logic runs entirely via Maven:

```bash
mvn rre:evaluate
```

→ `evaluation.json` is produced locally.
The `rre-server` is **optional**, useful for:

* Visualizing evaluations
* Hosting results via API (`POST /evaluation`)
* Exploring metadata via Swagger (`/swagger-ui/index.html`)

#### **How to generate `ratings.json` from a set of triples?**

**RRE does not provide a built-in tool for this.** If you already have a TSV/CSV file with:

```
query <TAB> doc_id <TAB> gain
```

→ You'll need to script the transformation manually, typically via Python or Groovy, to produce a valid hierarchical `ratings.json`.

---

### **Next Steps**

* [ ] Refine test documents to ensure query returns hits. [Use DOGE-5 test environment]
* [ ] Validate `match_query.json` against the actual corpus structure.
* [ ] Add more queries and documents to observe meaningful metrics. [Optional, only if DOGE-5 test environment not enough]
* [ ] Consider scripting the generation of `ratings.json` from annotated triples (.csv).

---

### **Attachments**

* `pom.xml`
* `ratings.json`
* `evaluation.json`
