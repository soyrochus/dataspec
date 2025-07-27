# Implement the following two changes

## 1) Implement the DataPath Lookup Function**

> **Prompt:**
>
> Write a Python function called `resolve_datapath` that, given a root data structure (according to the specs in the Yaml Data Schema Definition Syntax ), and a DataPath string as described below, returns the value at the specified location or raises an error if the path is invalid or not found.
>
> The DataPath syntax is:
>
> * Segments separated by dots (`.`) or slashes (`/`)
> * Array/list indices in square brackets, e.g., `[0]`
> * Map/dictionary keys in square brackets (e.g., `[2022]`, or `["foo"]` for strings)
> * Filters for arrays in the form `[field=value]`, matching the first array element with that property equal to the value
> * Chaining is allowed, e.g., `projects[id=543].epics[1].user_stories[0].priority`
>
> The function must support:
>
> * Arbitrary depth and nesting
> * Both integer and string keys
> * Both dot and slash as separators
> * Filters (`[field=value]`) and standard index/key selectors
>
> Examples:
>
> * `projects[0].epics[1].user_stories[0]`
> * `projects[id=543].epics[0].name`
> * `metrics[2022]`
>
> Return the found value or raise a KeyError/IndexError if the path cannot be resolved.

---

## **Good Function Names**

* `resolve_datapath`
* `get_by_datapath`
* `datapath_lookup`
* `find_by_datapath`
* `select_by_datapath`

**Recommendation:**

* Use `resolve_datapath` or `get_by_datapath` for clarity and convention.

---

## 2) merge the new function with the existing schema_val.py and turn them into a generic data defintion and search library

### Create a library (dir structure) called "dataspec"  using the existing code and the new DataPath search:


**Pitch:**
“With DataSpec you can validate, query, and explore any YAML, JSON, or Python structure—using expressive schemas and path navigation.”

**Requirements:**

* **Unify my existing data validation code** (schema-based validation of YAML/JSON/Python structures, including optional fields, typed maps, and arrays) with a new DataPath-based data search/query function (which allows pinpointing and extracting any value using an XPath/JSONPath-inspired syntax).

* **Support the following as core features:**

  * Schema validation, supporting my current schema format (as previously described, with no generic object, typed maps, required/optional, etc.).
  * DataPath-based querying/search, as described above, for retrieving any value or node from a nested data structure.

* **Library interface:**

  * Provide `validate(data, schema)` and `search(data, path)` as primary functions.
  * Accept Python objects, or load from YAML/JSON files/strings.

* **Command-line tool:**

  * The CLI entry point should be `dataspec`.
  * It must have at least two subcommands:

    * `validate` (same as current validation functionality; arguments: `--data` and `--schema`, both YAML/JSON)
    * `search` (new feature; arguments: `--data` and `--path`, print the value found or error)
  * Allow YAML/JSON for both data and schema, with auto-detection or optional explicit format flag.
  * Display clear, human-readable error messages for both validation and search.

* **Implementation priorities:**

  * Code must be modular, with reusable internal functions for parsing, validation, and path resolution.
  * Maintain or improve code quality and docstrings.
  * Write at least one usage example for both API and CLI in the README.

**Summary:**
Unify schema validation and data searching/querying for YAML/JSON/Python in a single `dataspec` library and CLI, using the above pitch as the project vision.




