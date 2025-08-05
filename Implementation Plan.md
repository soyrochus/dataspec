
# Test-Driven Implementation Plan for a PostgreSQL “TriStore” DSL and Runtime

## Overview and Objectives

The goal is to build a **generic DSL (domain-specific language)** and runtime in Python that interacts with a **PostgreSQL-based “TriStore”**. A TriStore in this context combines three data facets in one Postgres instance – **structured data (entities and attributes), graph relationships (Apache AGE extension), and vector embeddings (pgvector extension)** – to enable rich queries. The DSL will provide an abstraction for defining and querying this multi-model data store, serving both software developers and LLM agents (for example, an AI agent that can translate natural language into DSL queries). Key constraints and goals include:

* **100% Open-Source Components:** Use only open-source, industry-standard libraries (e.g., Lark for parsing, Psycopg for database access, etc.).
* **Python 3.10+ Implementation:** Develop the core as a reusable Python library.
* **Command-Line Interface (CLI):** Provide a CLI tool for interactive use or scripting.
* **Two-Phase Delivery:**

  1. *Phase 1:* Core schema definition and read-only query capabilities.
  2. *Phase 2:* Data modification (create/update) and vector similarity search features.
* **Test-Driven Development (TDD):** Adopt a milestone-driven, test-first approach – write tests for each feature milestone **before** implementation. This ensures reliability and that the design is verifiable from the start.

By following this plan, we will progressively build a robust DSL runtime that can be safely used by humans and AI agents alike to query and manipulate the TriStore.

## Architecture and Module Breakdown

To manage complexity, the project is structured into clear modules, each responsible for a part of the DSL or runtime functionality:

* **DSL Parser Module:** Uses Lark to define the grammar and parse DSL statements into an Abstract Syntax Tree (AST) or intermediate representation. Lark is chosen for its ease of defining grammar in EBNF form and built-in lexing/parsing. The grammar will cover entity/relationship definitions, query patterns, and data manipulation statements.
* **AST & Semantic Model:** Defines Python classes for the AST nodes (e.g., `EntityDef`, `RelationDef`, `Query`, `CreateOp`, `UpdateOp`, etc.) and performs semantic validation. This layer ensures the DSL statements make sense (e.g., references to entities/relations exist in the schema).
* **Runtime Engine:** Takes the AST and executes it against the PostgreSQL TriStore. This includes:

  * **Schema Manager:** Maintains metadata about defined entities and relationships (could be stored in-memory in Phase 1, and persisted or introspected from the database as needed). Responsible for **schema introspection** commands (showing defined entities/relations and their properties).
  * **Query Executor:** Translates read-only DSL queries into actual database queries. This will likely use Apache AGE’s Cypher queries for graph traversal and standard SQL for structured data. For example, a traversal DSL query might be converted to an `AGE_Cypher()` function call or a `SELECT ... FROM cypher(...)` query in PostgreSQL. The executor uses Psycopg to run these queries and fetch results.
  * **Data Manipulation Handler:** (Phase 2) Translates create/update DSL commands into SQL/Cypher insertions or updates. For instance, creating a new entity node uses an `INSERT` or Cypher `CREATE` query via AGE, updating a property might use Cypher `SET` on a node.
  * **Vector Search Handler:** (Phase 2) Integrates pgvector for similarity queries. Likely implemented by maintaining a vector store table (or embedding property) and using the `<->` or `<=>` vector distance operator in SQL queries. This component handles DSL commands like “FIND similar vectors ...”.
* **Database Connector:** Encapsulates the connection to Postgres (using `psycopg`). It may provide both synchronous and asynchronous query methods. Psycopg is a widely used adapter for Postgres in Python. We will use Psycopg3 (the modern version, imported as `psycopg`) for its async support and efficient usage in Python 3.10+.
* **CLI Interface Module:** Implements a CLI using Click (or argparse). Click is an industry-standard library for Python CLIs that makes it easy to compose commands and options. The CLI will leverage the DSL parser and runtime to allow users to run DSL commands from the command line or execute DSL scripts. It will be designed in a way that an LLM agent could also invoke it programmatically (e.g., via subprocess or by calling the Python API directly).
* **Testing Suite:** Not a runtime module but an important part of the structure. We will have a dedicated tests directory with unit tests for each module and integration tests that require a live Postgres with extensions. Pytest will be used as the test runner.

Each component is loosely coupled, interacting through well-defined interfaces (e.g., the parser produces an AST that the runtime engine consumes, the runtime engine uses the connector to talk to the DB). This modular design will make the system easier to maintain and enhance.

## Phase 1: Core Schema & Read-Only Queries

Phase 1 focuses on establishing the fundamentals: the DSL’s ability to define schema and perform read-only retrievals (traversals). It includes four main milestones, each developed with TDD:

### Milestone 1: Project Setup & Infrastructure

**Goal:** Lay the groundwork for development and testing.

* **Initialize Repository:** Set up a Python project structure (e.g., using Poetry or pip with a `pyproject.toml`). Create base packages (`tristore_dsl` for source, `tests` for tests).
* **Version Control & CI:** Configure Git and an optional CI pipeline (GitHub Actions) to run tests. Ensure the CI can spin up a Postgres with AGE and pgvector (perhaps using a Docker service in CI).
* **Testing Framework:** Configure Pytest. Write a trivial test (e.g., a sanity test for the CLI `--version` command returning the expected version) to verify the test harness is working.
* **CLI Entry Point:** Implement a minimal CLI using Click with a `--version` option and a placeholder command group. This will verify the packaging of a console script entry point (e.g., `tristore-cli`). Test this by invoking the CLI via `CliRunner` (Click’s testing utility).
* **Environment for DB:** Provide a Docker Compose file for local dev/test that runs PostgreSQL 16 with `pgvector` and `age` extensions enabled (the provided *TriStore* Docker image or Dockerfile can be used). No DB interaction yet, but verify the DB is accessible (maybe a smoke test that the psycopg connection can be opened). *No application logic yet beyond scaffolding.*

*Tests (Milestone 1):* Verify that:

* The CLI is discoverable and returns a version.
* A connection to the test database can be established (perhaps using a dummy query like `SELECT 1`).
* The project structure is importable (e.g., `import tristore_dsl` works).

### Milestone 2: Entity and Relationship Definition DSL

**Goal:** Enable users to define entities and relationships in the DSL, and store these definitions in the system. This provides the “schema” of our graph/structured model.

* **DSL Grammar (Definitions):** Use Lark to define grammar rules for statements like:

  * `DEFINE ENTITY <Name> (prop1 type, prop2 type, ...)` – to define an entity type and its attributes.
  * `DEFINE RELATION <Name> (<EntityA> -> <EntityB>)` – to define a relationship type (directed or undirected) between two entity types.

  The grammar will be defined in a Lark EBNF string. For example, we might define non-terminals for `entity_def` and `relation_def` and terminals for keywords like `DEFINE`, `ENTITY`, etc.
* **Parsing Logic:** Implement the Lark parser and write transformer classes or post-processing to turn parse trees into AST node objects (`EntityDef`, `RelationDef`). We will include rules to handle optional details (like maybe properties or relationship cardinalities if needed in future).
* **In-Memory Schema Registry:** Develop a SchemaManager component (in the runtime module) to store the defined schema. In Phase 1, this can be an in-memory store (e.g., dictionaries mapping entity names to attribute definitions, and relationship names to their endpoints). We will also consider immediately reflecting these definitions in the database:

  * On `DEFINE ENTITY`, we might create a **graph label** in AGE. Apache AGE doesn’t require explicit schema creation for labels (they are created when used), but we might choose to enforce schema by, say, creating a dummy node or maintaining a metadata table. Initially, we can simply record it internally and ensure actual data creation uses these definitions.
  * On `DEFINE RELATION`, similarly record the relationship type. AGE will consider any string as a relationship type when used; still, we manage a whitelist in SchemaManager to validate queries.
* **Test-First Development:** Before implementing, **write unit tests** for parsing and schema storage:

  * Example test: parsing `DEFINE ENTITY Person (name TEXT, age INT)` should produce an `EntityDef` object with name "Person" and the specified properties.
  * Test that after parsing and applying a `DEFINE ENTITY`, the SchemaManager knows about "Person" with correct fields.
  * Similarly for `DEFINE RELATION Friend (Person -> Person)` – AST should reflect source and target entity types, and SchemaManager should register this relationship.
  * Test error cases: defining a relationship with an unknown entity should raise an error (the parser or semantic analyzer should catch this).
* **Implementation:** Implement just enough code to pass the tests:

  * The Lark grammar and parser instantiation.
  * AST classes for definitions.
  * A simple SchemaManager (could be a singleton or part of a Context object) with methods like `add_entity` and `add_relation` that store definitions.
  * Basic semantic checks (e.g., no duplicate entity names, relation references valid entities). These checks can be tested as well.

*By the end of Milestone 2, we can parse schema definitions and hold them in memory.* No actual database changes are performed yet (aside from possibly ensuring the target graph exists in AGE, e.g., by running `SELECT * FROM ag_catalog.create_graph('main')` once).

### Milestone 3: Schema Introspection Queries

**Goal:** Allow the DSL to introspect and retrieve the currently defined schema (entities, relationships, their properties). This is important both for developers and for LLM agents to understand what data model is available.

* **DSL Grammar (Introspection):** Add grammar rules for statements like:

  * `LIST ENTITIES` – returns all defined entities and their properties.
  * `LIST RELATIONS` – returns all defined relationships and their endpoint types.
  * Possibly `DESCRIBE ENTITY <Name>` – show details of one entity type.

  These commands will not require complex parsing (mostly keyword-based).
* **Execution Logic:** Implement handlers in the runtime engine to format the schema info. The SchemaManager can supply the data (from Milestone 2’s stored definitions). The output can be simple text or structured data. For CLI, we may format as tables; for programmatic use, as Python dicts/lists.
* **Database Introspection (optional):** For Phase 1, the primary source of truth is SchemaManager’s records. However, we should verify alignment with the actual database. Write integration tests to ensure that if a user defined an entity and then created some data (Phase 2), the introspection still matches. (Strict DB-backed introspection can be deferred to Phase 2, where we might introspect actual tables or graph metadata.)
* **Test Plan:** Write tests to ensure:

  * After defining entities/relations, `LIST ENTITIES` returns the correct set (order or format can be normalized for testing).
  * `LIST RELATIONS` shows each relation with correct endpoints.
  * Defining multiple entities then listing shows them all.
  * If no entities defined, listing returns empty list or a message.
* **Implement:** Code the introspection commands:

  * Likely functions like `get_entities()` and `get_relations()` in SchemaManager.
  * Integrate these with CLI: e.g., `tristore-cli schema list` could call these and print results.
  * Ensure the output is clear and developer-friendly (e.g., each entity with its properties and types). Keep output parseable as well (for LLM consumption, a consistent format like YAML/JSON or markdown table may help, but initially plain text is fine).

*This milestone solidifies the DSL’s ability to introspect itself,* which will also help in Phase 2 when LLMs might ask “what is the schema?” to formulate queries.

### Milestone 4: Read-Only Traversal Queries

**Goal:** Support querying the data (which by Phase 1 will mainly be graph traversal queries since no data creation DSL yet, but we will seed some test data directly to test queries). Traversal queries should allow exploring relationships among entities without side effects.

* **DSL Query Grammar:** Define grammar for at least basic graph pattern queries. Possible approaches:

  * Cypher-like pattern: e.g., `FIND Person WHERE name="Alice" -> Friend -> Person;` meaning find Persons related via Friend relation from Alice.
  * Or a more function-like syntax: `QUERY MATCH (p:Person)-[:Friend]->(q:Person) RETURN q;` (which is essentially Cypher itself).

  We need to decide on a **simplified DSL syntax** that’s easier and safer than full Cypher (especially for LLM usage). For instance, the DSL might only allow predefined relationship traversals rather than arbitrary Cypher expressions. **Example DSL**: `GET FriendsOf("Alice")` or `TRAVERSE Person[name="Alice"] -Friend-> Person` – this would return persons who are friends of Alice. We will design the grammar to cover selecting a starting set of entities by attribute filter and following one or more relationships.
* **Semantic Checks:** Ensure the query references valid entity types and relationship names as per the schema. The AST for a query might include nodes for the starting condition and the path of relationships to traverse.
* **Query Execution:** Translate the DSL query into actual database queries:

  * If using Apache AGE’s Cypher: The runtime can compose a Cypher `MATCH` query. For the above example: `MATCH (p:Person {name:"Alice"})-[:Friend]->(q:Person) RETURN q`. This can be executed via AGE’s functions. Since Apache AGE supports openCypher in SQL, we can call `SELECT * FROM cypher('graph_name', $$ MATCH ... $$) as (q agtype);`. The `agtype` result can be parsed via the AGE driver or psycopg.
  * Alternatively, we could use the Apache AGE Python driver (`age` library) as shown in the Apache AGE blog. However, to keep components standard, using direct psycopg calls to AGE’s cypher function is fine.
  * For purely relational queries (if any structured data not in graph), we could use SQLAlchemy or direct SQL. Phase 1 might not emphasize this, focusing on graph traversal.
* **Testing (Unit):** Write parser tests for various query forms:

  * Proper AST generation for a simple one-hop query.
  * More complex query (multi-hop traversal if supported, e.g., `A -> R1 -> B -> R2 -> C`).
  * Filtering by property values (like name="Alice").
  * Invalid queries (unknown entity or relation) should be rejected (test that it raises an error).
* **Testing (Integration):** Before implementation, plan how to test actual query execution:

  * We need sample data. Since Phase 1 DSL does not create data, we can **seed the database** in the test setup. For example, using Psycopg or the AGE driver, insert a few nodes and edges (e.g., create Person nodes "Alice" and "Bob", and a Friend relationship between them). The integration test can do this in a setup step (perhaps by executing Cypher directly).
  * Then, test that running our DSL query (via the runtime engine) returns expected results. For instance, `TRAVERSE Person[name="Alice"] -Friend-> Person` should yield "Bob" given the seed data.
  * Ensure vector extension doesn’t interfere (we can create the extensions in the test DB, but not use vector yet).
* **Implement Query Support:**

  * Expand the DSL parser for the query syntax.
  * Implement execution in the runtime: the Query Executor will map AST to a SQL string or use a library call. For early simplicity, we can construct a Cypher query string and execute with psycopg. (We will need to ensure the Postgres session has the AGE extension loaded and a graph created; this can be done once at startup: `CREATE EXTENSION age; SELECT * FROM ag_catalog.create_graph('main');` in init SQL).
  * Parse results: The results from AGE’s cypher come as `agtype` values which might be returned as strings in JSON format. We may need to parse those into Python dicts or into our own Entity instances. The Apache AGE driver’s `age` library could help (it might parse agtype to Python automatically), or we handle it by enabling the `age` extension’s type adapter in psycopg.
  * Support simple projections: e.g., return entire node or specific properties. For now, returning the node or a property set is fine.
* **Output Format:** The CLI should display query results in a readable form (e.g., list of nodes with properties). For programmatic use, the runtime can return Python objects or dicts.

By completing Phase 1, we will have:

* A defined DSL grammar and parser for schema and read-only queries.
* In-memory schema tracking (with potential to extend to persistent).
* The ability to execute graph traversal queries on existing data.
* Comprehensive tests ensuring each part works (from parsing to execution).

**Phase 1 Deliverables:**

* Users can define a schema (entities/relations), list the schema, and run traversal queries (assuming data is present).
* All features have corresponding unit tests (e.g., parser tests, schema manager tests) and basic integration tests with Postgres/AGE for query execution.

## Phase 2: Data Mutation & Vector Search Enhancements

Phase 2 will extend the DSL and runtime to allow modifying data and performing vector similarity searches. It builds on Phase 1, so it assumes the basic query capability is working. New milestones in Phase 2:

### Milestone 5: Data Creation Commands

**Goal:** Enable DSL commands to insert new data into the TriStore – both entities (nodes) and relationships (edges).

* **DSL Grammar (Create):** Add rules for statements like:

  * `CREATE ENTITY <Type> (property1=value1, property2=value2, ...)` – to create a new node of a given entity type.
  * `CREATE RELATION <RelType> (from <EntityType> id <X> to <EntityType> id <Y>)` – or an alternative syntax to create a relationship between two existing entities. Perhaps we allow referencing nodes by some identifier or unique property.

  We need a way to identify existing nodes; since we don’t have a full identity concept in DSL yet, one approach is to allow a match-then-create in one statement (like Cypher’s `MERGE` or `MATCH ... CREATE`). Simpler: require the user to provide some unique key property in the create command, or we add an implicit ID.
* **Execution – Creating Nodes:** For a `CREATE ENTITY Person (name="Charlie", age=30)`, the runtime will formulate a SQL/Cypher insertion:

  * Using AGE, we can do `SELECT * FROM cypher('main', $$ CREATE (p:Person {name:'Charlie', age:30}) RETURN id(p) $$) as (id agtype);` – to insert and get an internal ID. Or using the `age` Python library: `connection.execCypher("CREATE ...")`.
  * Alternatively, we could use standard SQL INSERT into underlying tables (AGE stores vertices in a table like `<graph_name>_vertex`, but that’s internal; better to use Cypher).
* **Execution – Creating Edges:** For creating a relationship, we likely need to identify the start and end nodes. If the DSL knows some unique property, e.g., `CREATE RELATION Friend (from Person WHERE name="Alice" to Person WHERE name="Bob")`. We can implement this by first finding those nodes (perhaps the runtime will do a lookup query by that property) then create the edge:

  * Cypher example: `MATCH (a:Person {name:'Alice'}), (b:Person {name:'Bob'}) CREATE (a)-[:Friend]->(b);`.
  * We should define whether the DSL will handle multiple matches (likely we assume unique matches for simplicity).
* **TDD Tests:**

  * Unit tests for parser: e.g., ensure `CREATE ENTITY Person (...)` string yields a CreateOp AST with correct type and properties.
  * Integration tests:

    * Start with an empty database (or known state), run a DSL create command, then directly query the DB (via Cypher or SQL) to verify the data exists. For example, after `CREATE ENTITY Person (name="Dave")`, a Cypher `MATCH (p:Person {name:"Dave"}) RETURN p` should find a node.
    * Test creating an edge after creating some nodes. Verify the relationship exists (e.g., by a Cypher query or by our own traversal DSL).
    * Test error conditions: creating an entity of undefined type (should error), creating a relation with undefined endpoints, etc.
* **Implement Create:**

  * Extend the runtime engine with a `create_entity` method: builds and executes the appropriate query.
  * Possibly generate IDs for new nodes. We might not expose internal IDs in DSL, but maybe return a reference that can be used in the session. The simplest is to return the newly created node’s properties (including any primary key if available). AGE can give an internal id, but those ids are not easily reused outside Cypher context. Instead, if the entity type has a natural key (like `name` in Person), we rely on that to find it later. (We may consider adding an implicit unique ID property to all entities, like an auto-generated UUID, and return that.)
  * Extend SchemaManager if needed to track if any default properties or constraints (not too deep for now).
  * Ensure transactional behavior: likely each DSL statement execution runs in its own transaction (psycopg commit) unless a multi-command script is executed.

After this milestone, users/LLMs can add data to the knowledge graph via the DSL.

### Milestone 6: Update/Annotation Commands

**Goal:** Support modifying existing data – updating properties of nodes or relationships, or annotating with new information (including possibly adding JSON or vector data as attributes).

* **DSL Grammar (Update):** Add syntax such as:

  * `UPDATE <EntityType> WHERE <condition> SET <prop>=<val>, <prop2>=<val2>;` – to update properties on one or multiple nodes that match a condition.
  * `UPDATE RELATION <RelType> ...` – possibly to update relationship properties if any (or this might not be needed if relationships are mostly just connections).
  * If “annotate” is a separate concept (for example, attaching a vector embedding to an entity), we could have `ANNOTATE <EntityType> WHERE ... WITH VECTOR <vectorName>;` or simply treat it as a special case of update (setting a vector property).
* **Execution:**

  * For node property updates: translate to a Cypher `MATCH ... SET ...` statement. E.g., `MATCH (p:Person {name:'Alice'}) SET p.age = 31`.
  * If multiple nodes can match, decide if we allow that (maybe yes, update all matching).
  * For adding new properties (annotation), Cypher `SET` can add new keys on the fly (since properties are dynamic). So `SET p.newProperty = "value"` is possible.
  * For vectors: We have two options:

    1. **Store vector in the graph property** as some array type if AGE’s agtype supports it. (AGE’s agtype is JSON-like, it might support lists of floats, which could represent a vector. We should confirm AGE can store a list as a property.)
    2. **Store vector in a separate SQL table using pgvector**, linked by an entity ID. For example, maintain a table `entity_vectors(entity_type, entity_id, embedding vector(768))`. In this approach, an “ANNOTATE ... WITH VECTOR” DSL command would actually do an SQL `INSERT` or `UPDATE` on that table. We would also need to retrieve it in vector searches.

    Using pgvector’s **vector type** is advantageous for indexing and similarity search. So likely we choose option 2: have a dedicated vector store table for each entity type (or a generic table with entity reference).
  * If we use a separate table, the runtime needs to know the mapping between an entity and its vector. One approach: assume each entity has a unique identifier (like a UUID or the internal AGE id if we can get it). We could create a mapping using that ID. Alternatively, require the DSL user to provide the vector along with the entity creation (not likely).
  * For now, implement a simple mapping: e.g., if an entity type has a property that is marked as “vector”, we store it in a pgvector column. This implies schema definitions could allow a property type like VECTOR(n). We might extend `DEFINE ENTITY` to support a vector type property in Phase 2.
* **TDD Tests:**

  * Unit tests for parsing update statements (various forms: one property, multiple, annotate).
  * Integration test:

    * Create an entity via DSL, then update it via DSL, then query (via DSL or direct SQL) to see if the change took effect.
    * For vector annotation: create an entity, annotate with a sample vector, then query the vector table directly to ensure it’s stored, or attempt a vector search (next milestone).
    * Test updating a non-existent target (should result in no-op or error? Possibly we signal if no records found).
    * Test that incorrect syntax or unknown fields are handled.
* **Implement Update:**

  * Extend the parser for `UPDATE` (and possibly `ANNOTATE` unless we unify it).
  * In runtime, for a given update AST:

    * If it’s a regular property update, generate a Cypher `MATCH...SET` and execute via psycopg.
    * If it involves a vector, extract the vector (which might be given as a list of numbers in the DSL or a reference to some named vector variable in context). Then store it:

      * If we decided to store in graph, do `SET p.embedding = [0.1,0.2,...]` (if agtype supports).
      * If using pgvector table, do an `INSERT ... ON CONFLICT ... UPDATE` in the embeddings table for that entity. We need the entity’s ID for this. Possibly retrieve the internal id in the MATCH and then do a separate SQL. This may require two DB calls (or use a CTE to do both in one statement if advanced).
    * Ensure the transaction covers both operations if separate queries (use psycopg transaction or explicit SQL transaction block).
  * Provide feedback: The CLI could output how many nodes were updated or similar.

After Milestone 6, the DSL can modify the data graph. This unlocks the ability for an LLM agent not just to query but also to insert new info or update as it reasons (subject to user’s permission, presumably).

### Milestone 7: Vector Similarity Search

**Goal:** Use the pgvector extension to find entities with embeddings similar to a given vector or to another entity’s embedding. This adds a powerful semantic search capability to the DSL.

* **DSL Grammar (Vector Search):** Introduce a syntax for vector queries. Possibilities:

  * `SEARCH <EntityType> NEAR <vector_literal> [LIMIT N]` – to find the top N entities of that type with embeddings nearest to the given vector.
  * Or `FIND <EntityType> SIMILAR TO "<text or item>"` – if we integrate embedding generation (likely out of scope to generate in DB; assume vector is given).
  * We might also allow something like `SEARCH <EntityType> NEAR <EntityType>[id=X]` to find similar to a specific existing entity’s vector.
* **Execution:**

  * This will be a SQL query using the `<->` operator provided by pgvector for nearest neighbor search. For example: `SELECT id, embedding FROM person_embeddings ORDER BY embedding <-> '[0.2, 0.1, ...]'::vector LIMIT 5;` would retrieve the 5 closest vectors. We then map those back to entity IDs and perhaps fetch the corresponding entity data.
  * If vectors are stored as properties in the graph (agtype), we’d have to pull all and compute similarity in Python, which is inefficient. So using pgvector column with proper index (HNSW or IVFFlat index on that column) is ideal.
  * We will likely maintain one table per entity type for embeddings (e.g., `person_vector` with schema (entity\_id BIGINT, embedding VECTOR(768))). Alternatively, one big table with an entity type field.
  * Ensure that whenever we create or update an entity’s vector property, we also update this table. (This was partly done in Milestone 6’s annotation.)
* **Integration with Graph:** After getting a list of similar entity IDs, the DSL might want to allow further graph traversal. In this milestone, we can focus on just retrieving the similar entities, and optionally the user can then use a normal query to get more info on them.

  * We could enhance the DSL like: `SEARCH Person NEAR [vector] RETURN name, age` to directly fetch some fields of those persons. This means joining the vector query result with actual entity data.
  * Implementation: do a subquery or two-step: find IDs by vector search, then match those IDs in AGE to get properties. AGE internal IDs might not align with the primary keys we use in vector table unless we use the same. Perhaps simpler: if we have assigned a UUID or our own ID to each node on creation, use that as the link (store that in vector table too).
* **Tests:**

  * Unit test the parser for `SEARCH ...` statements (with vector literal input, etc.).
  * Integration test:

    * Populate some entities with known vectors (we can use small 2D or 3D vectors for simplicity in tests). For example, Person A with vector \[0,0], Person B with \[1,1], Person C with \[5,5]. Query for near \[0.1, 0.1] should return A and B before C.
    * Ensure the DSL search returns the expected IDs or names.
    * Test limit works (e.g., only top N returned).
    * Test searching an entity type that has no vectors stored yields an empty result or error (depending on design).
* **Implement:**

  * Extend grammar and parser for the search command.
  * In runtime, implement a `vector_search(entity_type, vector, topN)` function:

    * Compose the SQL: e.g., `SELECT entity_id FROM <entity_type>_vectors ORDER BY embedding <-> %s LIMIT %s`.
    * Execute via psycopg (use `execute()` with parameters to avoid SQL injection).
    * Fetch the resulting IDs. Then possibly fetch entity details: we can either:

      * Have the vector table also store some reference to the actual table row or have identical IDs. If using AGE internal ids, we could fetch the nodes by id via Cypher `MATCH (n:Person) WHERE id(n) = X RETURN n`.
      * Or if we introduced a custom UUID (which we stored as a property and also in vector table), we can match by that property.
    * For now, to keep it simple: use AGE’s global id if accessible. According to AGE documentation, each node has a function `id(n)` that gives a unique identifier. We saw an example output in the blog: `id:844424930131969`. We could potentially use those as the `entity_id` in the vector table. If so, we can directly use those for matching.
    * Return or print the results. The CLI can show a list of entity identifiers or names. For more user-friendly output, perhaps directly show the top result's properties.
  * Ensure an index is created on the embedding column for performance (perhaps part of the setup or creation of the table, using `CREATE INDEX ON person_vectors USING ivfflat (embedding vector_cosine_ops) WITH (lists=100)` or similar — this could be part of deployment instructions rather than dynamic in code).

After this milestone, semantic vector search is available through the DSL, completing the TriStore trifecta: structured/graph querying plus vectors. Developers or LLM agents can ask for “similar items” and then traverse relationships among them, all via our unified DSL.

### Milestone 8: CLI & Integration Polishing

*(Optional, could be part of finalizing Phase 2)*

By now, the CLI likely has multiple subcommands or a REPL-like interface. This milestone ensures the CLI is user-friendly and that all components work together smoothly:

* Implement a **REPL mode**: If beneficial, allow running `tristore-cli` with no arguments to drop into an interactive prompt where users can type DSL commands and see results. This can aid manual testing and also be a channel for an LLM (which could send commands one by one).
* Organize CLI commands: Possibly we have subcommands like `tristore schema define` (for DEFINE statements) or we simply accept any DSL command as an argument. An alternative is a single `tristore exec "<DSL statement>"` interface. We should decide and document it. Using Click, we can have subcommands or options:

  * e.g., `tristore run file.dsl` to execute a script file of DSL commands.
  * `tristore query "FIND Person ..."` to run a one-off query.
  * `tristore load example_data.yaml` for future data loading, etc.
* Add **help and documentation** to CLI: Use Click’s help features to describe each command. Ensure running `tristore-cli --help` shows usage.
* Ensure **logging and error handling**: The runtime should catch exceptions (like SQL errors, parse errors) and report them nicely (especially in CLI context, no stack traces for user, but useful info for debugging).
* **Integration Test Full Workflow:** Write a higher-level test scenario that:

  1. Defines a schema (entities/relations),
  2. Creates some instances,
  3. Runs a traversal query,
  4. Updates an instance,
  5. Runs a vector search (if applicable),

  and asserts that each step’s output is correct. This end-to-end test ensures all pieces work together. It might be implemented in a pytest function that calls the CLI commands via `CliRunner.invoke` or calls the library functions directly.
* **Performance considerations:** While not heavily tested in this scope, mention that for larger scale, we should consider using indexes (ensure pgvector index, possibly using `CREATE INDEX` in an initialization step for each vector column) and maybe adding indexes on frequently queried properties.

By the end of Phase 2, the DSL and runtime should be feature-complete according to the requirements: we can define schema, create and update data, traverse relationships, and perform similarity searches. All is accomplished with open-source tools (PostgreSQL, AGE, pgvector, Python libraries) and is packaged in an easy-to-use library and CLI. Extensive tests will give confidence in the correctness of each part.

## Recommended Tools & Libraries

Throughout the implementation, we leverage the following open-source libraries and tools:

* **Lark Parser** – for defining the DSL grammar and parsing input. Lark allows writing grammars in a high-level notation and handles lexing/parsing internally. It’s well-suited for building DSLs quickly. We prefer it over writing a manual parser to speed up development and ensure correctness.
* **Psycopg (psycopg3)** – for PostgreSQL database connectivity. Psycopg is the standard Python adapter for Postgres and fully open-source. The newer version psycopg3 has async support and other improvements, which could be useful if we later allow async query handling. We will use it in standard (sync) mode for simplicity, managing transactions manually as needed.
* **Apache AGE** – the Postgres extension providing graph database features (Cypher query support). We rely on AGE to store and query the graph relationships (nodes and edges representing entities and relations). The Apache AGE Python driver (`age` library) can be optionally used for convenience, but we can also interact via raw SQL and the `cypher()` function.
* **pgvector** – Postgres extension for vector similarity search. It introduces the `vector` data type and distance operators for nearest-neighbor queries. This is crucial for Phase 2 vector search. We will use it by creating tables/columns of type `VECTOR(n)`. No separate Python library is needed; operations are done via SQL.
* **SQLAlchemy (optional)** – for certain parts like schema reflection or constructing SQL queries programmatically. For example, SQLAlchemy could be used to manage a SQLite memory DB for unit tests (if we simulate some functionality) or to reflect the Postgres schema if we wanted to introspect existing tables. It’s mentioned as an industry-standard, but we can limit its use to avoid complexity. Perhaps we use it for structured data in the future or to build query strings safely. In the TigerData tutorial, SQLAlchemy is suggested for ORM usage, but in our case we mostly hand-write queries due to Cypher usage. We will mention it as a potential tool for expansion.
* **Click for CLI** – to implement the command-line interface. Click is widely used to create user-friendly CLI apps with minimal boilerplate. It will handle command parsing and help text. It also provides a testing utility (CliRunner) to simulate CLI calls in tests.
* **pytest** – for writing and organizing tests. Pytest’s powerful fixtures and assertions will be used throughout. We may also use plugins like `pytest-docker` or `pytest-postgresql` to manage the Postgres instance in tests.
* **Docker** – to run the Postgres database with required extensions in development and CI. We will likely maintain a Dockerfile (or use the one from the provided step-by-step guide) to ensure a reproducible environment with PostgreSQL 16 + AGE + pgvector. This environment will be used for integration tests and can be recommended for users to run the system.
* **Development Utilities:**

  * Linters/Formatters like Flake8/Black to maintain code quality.
  * Possibly MyPy for type checking (optional but helps with reliability).
  * Makefile or tasks for common commands (test, run, etc.)
  * `pre-commit` hooks to enforce standards on every commit (optional, but useful).

These tools ensure the project remains aligned with best practices and is accessible to other contributors. All components are open-source, satisfying the OSS requirement.

## Testing Strategy

The project will be developed with a **Test-Driven Development (TDD)** approach at its core. This means writing tests for each feature **before** implementing the feature, then writing the minimal code to pass the tests. The testing strategy is divided into two levels:

* **Unit Tests:** For each module and function, covering the logic in isolation. For example:

  * Parser tests: feed known DSL strings and verify the AST output matches expectations.
  * Schema manager tests: after a sequence of definitions, verify the stored schema.
  * Query builder tests: given an AST for a query, verify the generated Cypher/SQL string is correct (this could be done by inspecting a function result before execution).
  * These tests will use mock objects or stubs where needed (though for many, we can use real instances since there’s no external dependency except DB).
  * Fast execution, no database required (except we might use a fake in-memory repository for schema or simulate a DB for certain checks). This keeps iteration quick.

* **Integration Tests:** These tests involve the running PostgreSQL database with AGE and pgvector. They test end-to-end scenarios:

  * We will mark these tests, e.g., with `@pytest.mark.integration` so they can be separated from unit tests. They will require environment variables or fixtures that provide a database connection.
  * Integration tests include:

    * Schema definition commands followed by a direct DB introspection to ensure, for instance, that creating an entity doesn’t inadvertently create a SQL table (in Phase 1, it shouldn’t, in Phase 2, creating an entity might insert a node which we can verify via a Cypher query).
    * Full query execution: e.g., populate some data (either through DSL in Phase 2 or via raw SQL in setup), then run a DSL query via the CLI or the runtime API, and check the output.
    * Vector search: insert vectors, run search, verify results.
    * CLI end-to-end: using Click’s `CliRunner`, simulate a user session:

      * e.g., `tristore-cli exec "DEFINE ENTITY ..."`, then another call to `exec "CREATE ENTITY ..."` etc., and ensure no errors and expected output at each step. This tests the CLI parsing and integration with the core library.
  * We will use **fixtures** to manage the database state. For example, a `db` fixture could start a Docker container (if not already running) or use an already running test DB, ensure the required extensions are enabled (via the init SQL that creates `EXTENSION vector` and `EXTENSION age`), and yield a connection string. After tests, it can clean up (drop graph or tables to isolate tests).
  * Consider using **Testcontainers** or `docker-py` to automate bringing up the Postgres with extensions for tests. Alternatively, require the developer to have it up and use a known DSN.

* **Coverage:** We aim for high test coverage (especially of parsing and logic layers). Every new feature in a milestone is considered done only when its tests pass. Each milestone’s completion criteria includes running the full test suite to avoid regressions.

* **Test Data Management:** Since we are dealing with a database, managing test data is crucial. We will:

  * Use transactions or savepoints in integration tests to roll back changes after each test (if possible, e.g., using Psycopg’s connection in autocommit off and rollback at end).
  * Alternatively, each test can operate in its own schema or graph: Apache AGE supports multiple graphs, so we could create a unique graph name per test (like “test\_graph\_123”), use it in queries, and drop it after. This isolates graph data. For vector tables, include the test identifier in the table name if needed.
  * Keep vector dimensions small in tests (for speed and simplicity, e.g., 3 or 5) and use simple numeric data.

* **Continuous Integration:** Set up a CI pipeline that:

  * Spins up the Postgres with AGE+pgvector (maybe using the Docker image built in dev).
  * Runs `pytest` for unit tests quickly.
  * Then runs integration tests (possibly in a separate job or with an marker selection).
  * We will also run linters in CI.

This rigorous testing approach ensures each part of the implementation is correct and that changes can be made with confidence. It also makes the system more reliable for use by LLM agents, as any misunderstanding by an AI (sending a wrong query) can be caught if it doesn’t conform to the grammar or schema – our system will provide clear error messages rather than silent failures.

## CLI Design and Usage

The CLI serves as both a user-friendly interface and an executable entry point for automation or agent integration. Key aspects of the CLI design:

* **Entry Point:** The console script (installed via pip as part of the library) will be named, for example, `reagent` or `tristore`. (We’ll assume `tristore` here for clarity.)
* **Command Structure:** Using Click, we design the CLI with subcommands for logical groupings:

  * `tristore define`: Commands related to defining schema.

    * `tristore define entity <Name> <props>` – Alternatively, we may not need this if we allow free-form DSL, but having a dedicated command can provide help. However, maintaining two ways (CLI options vs. DSL text) is extra work. Instead, we might use a single `exec` interface as below.
  * `tristore query "<DSL query>"`: Execute a read-only query and print results.
  * `tristore exec "<DSL statement>"`: Execute any DSL statement (create, update, query, etc.). This is a general entry where the CLI just passes the string into the parser and runtime.
  * `tristore file <filename.dsl>`: Execute a file containing multiple DSL statements (each terminated by `;` or newline). This allows scripting a sequence of operations, which is useful for seeding data or running complex operations.
  * `tristore schema` subcommands:

    * `tristore schema list` – equivalent to `LIST ENTITIES` and `LIST RELATIONS`, could print a summary of the schema.
    * Or separate `tristore schema entities`, `tristore schema relations`.
  * Possibly shortcuts like `tristore vectors import <file>` if we wanted to bulk load embeddings from a file (beyond scope).

  Given the DSL is the core, one design is to have a single command mode: if you run `tristore-cli` with an argument that is not a defined subcommand, interpret it as a DSL command. Click allows catching unknown subcommands, but a cleaner way: provide an `--execute` option. Alternatively, implement an interactive shell if no args given.
* **Interactive Mode:** If the user runs `tristore` with no arguments, open a REPL. We can use Python’s `cmd` library or just a loop reading input. This REPL can have basic line editing (or use a library like `prompt_toolkit` for fancy features, though that adds a dependency). The REPL will accept DSL commands and output results continuously.

  * This is helpful for manual exploration. For an LLM agent, it might be easier to call non-interactively, but a REPL could simulate a conversational agent that the LLM controls.
* **CLI Output:**

  * Use human-readable tables or lists for results. E.g., printing entities in a markdown-like table:

    ```
    +----------+--------------------+
    | PersonID | name    | age      |
    +----------+--------------------+
    | 1        | "Alice" | 30       |
    +----------+--------------------+
    ```

    For graph traversals, perhaps list each result path or node.
  * For schema introspection, listing each entity and its properties in a clear format (maybe each on new line, or as a YAML).
  * Since LLM agents might parse the output, we might provide a flag to output JSON for any command. E.g., `--json` option to output results in machine-friendly JSON. This could be very useful for integration tests and for any tool consumption.
* **Examples and Help:** Provide examples in the README or `--help`. For instance, `tristore query "TRAVERSE Person[name='Alice']-Friend->Person"` example usage. Also mention that environment variables or config file can be used for DB connection (the CLI might allow `-h host -p port -d database -U user` options to connect to a non-default DB).
* **Configuration:** The CLI will by default connect to a local Postgres (e.g., `localhost:5432` and a default database name). We’ll allow overriding these via options or env vars (like `PGHOST`, `PGUSER`, etc., or a `.env` file).
* **CLI Testing:** We will test the CLI using Click’s testing utilities. For example, ensure that `tristore exec "LIST ENTITIES"` returns the expected text when some entities are defined (setup within the test).
* **Robustness for Agents:**

  * Keep output as deterministic as possible (e.g., sorted order of items when listing, unless there’s a reason to preserve a creation order).
  * Avoid extraneous info in output (agents prefer just the data asked for).
  * The DSL and CLI will not require interactive confirmation or such (except maybe for dangerous operations, which we can avoid implementing or require a flag).
  * If an LLM is to use this, it will likely produce DSL commands which our parser will strictly enforce. Any syntax error will yield a clear error message, which the LLM or calling system can catch and possibly recover from. This is a safer interface than letting an LLM run raw SQL because the DSL constraints what operations are possible to those we implemented and tested.

In summary, the CLI is a thin wrapper around the DSL runtime, ensuring that whether a developer types a command or an LLM formulates one, it gets correctly parsed and executed, and the results are presented clearly. The CLI also serves as a convenient entry point for deployment (one can run it in Docker or on a server to process commands, etc.).

## Deployment and Development Environment

To ensure the project is easy to set up and deploy, we outline the environment setup, deployment strategy, and developer workflow:

* **Local Development Setup:**

  * Use a Python virtual environment (Python 3.10+). Developers will install the library in editable mode (e.g., `pip install -e .`) to do rapid development.
  * Provide a `requirements.txt` or use Poetry’s lockfile to pin dependencies (Lark, psycopg, click, etc.).
  * Use the provided Docker Compose to run Postgres with required extensions. For example:

    ```yaml
    services:
      db:
        image: tristore-pg:latest  # built from our Dockerfile that includes AGE+pgvector
        environment:
          POSTGRES_PASSWORD: example
        ports:
          - "5432:5432"
    ```

    The Dockerfile (from the step-by-step guide) compiles AGE and installs pgvector. We will include this Dockerfile in the repo for reference. If using a pre-built image (like `apache/age`), we might need to install pgvector on top – our custom image ensures both are present and auto-enabled via an init script.
  * The init SQL (`init-tristore.sql`) will run `CREATE EXTENSION vector; CREATE EXTENSION age;` on database startup, so that the extensions are available by default.
  * Developers should configure the DSN (host, user, password) for the running DB. We can default to `user=postgres, password=secret, host=localhost, port=5432, dbname=postgres`. Documentation will instruct how to change this if needed.
  * Ensure Apache AGE’s search path or usage: typically, one must do `SET search_path = ag_catalog, "$user", public;` or use the `age` schema. The AGE quickstart suggests how to use it, but using the `cypher('graphname', $$...$$)` function should automatically use AGE if the extension is loaded.
* **Continuous Integration Environment:**

  * The CI (e.g., GitHub Actions) can use a service container with Postgres. If our custom image is published or built in CI, we use that. Alternatively, have CI run the Dockerfile build and run container as a step.
  * CI should set up the DB and run tests. Any failing test will prevent deployment.
* **Packaging and Distribution:**

  * Use standard packaging so that the library can be installed via pip. That includes proper `setup.py` or `pyproject.toml` with entry points for the CLI.
  * Choose a license (likely an OSS license such as MIT or Apache 2.0, given all components are OSS).
  * We might publish the package to PyPI for easier installation. Also, provide instructions to install PostgreSQL with the needed extensions (for those who want to deploy without Docker).
* **Documentation:**

  * Create a README.md with usage examples, installation steps (e.g., how to build the Docker image and run it, how to install the Python package, a quick example of defining a schema and querying).
  * Possibly host documentation (using e.g., Sphinx or MkDocs) for the DSL syntax and developer guide.
  * Provide schemas or EBNF of the DSL grammar in the docs for clarity (useful for LLMs too, as they can be given the grammar to constrain their output).
* **Dev Workflow:** Encourage contributors to use the test-first approach. Possibly include a `CONTRIBUTING.md` outlining coding style, how to run tests, etc.
* **Deployment Use-Case:** In a production scenario, the library would be integrated perhaps into a larger system (like the ReAgent context-engineering system). Deployment might involve:

  * Ensuring the Postgres instance is running with the extensions.
  * Installing the Python package in the environment where the agent or application runs.
  * Using the CLI or library API to handle queries. For example, an LLM agent could call a Python function to execute a DSL query and get results to include in a prompt. We will make sure the library API is straightforward (e.g., `from tristore_dsl import execute` which accepts a DSL string and returns results).
  * The CLI could also be deployed as a microservice (one could wrap it in something like a Flask API if needed, though that’s beyond our scope, but the design doesn’t preclude it).
* **Maintaining OSS Compliance:** All chosen components are OSS. We will clearly attribute them in LICENSE or NOTICE files as required (especially Apache AGE (Apache License) and any others).
* **Developer Utilities:** Possibly include scripts to regenerate grammar from Lark (though Lark doesn’t need separate generation, it’s runtime). Also, if using ANTLR for any reason (if not Lark), we’d include the grammar file. But Lark is simpler here.

Lastly, we ensure that the overall implementation is not only actionable but also adaptable. The plan allows incremental progress (milestones), each adding functionality while keeping the system functional, which is crucial for validation and for any AI agent that might be learning to use the DSL. By Phase 1 end, one can already query (read-only), and by Phase 2 end, the full spectrum of operations is available. This progressive enhancement means that at each stage, documentation and tests are updated, and potentially an LLM could be fine-tuned or instructed with the new capabilities.

## Conclusion

This implementation plan provides a comprehensive roadmap for developing a Python-based DSL and runtime for a PostgreSQL TriStore (relational + graph + vector). By using test-driven development and breaking the work into milestones, we ensure each feature is well-designed, tested, and integrated. The use of proven libraries (Lark, Psycopg, Click, etc.) and PostgreSQL extensions (Apache AGE, pgvector) aligns with industry best practices and open-source standards. The final deliverable will be a reusable Python library and CLI tool that can be used interactively by developers or programmatically by LLM agents to query and manage a knowledge repository that combines structured data, relationships, and semantic vector search.

Through this phased, test-first approach, the project will result in a robust, maintainable system. It will empower users to define rich schemas, store and update data, traverse knowledge graphs, and leverage vector similarity – all through a coherent DSL that abstracts the underlying SQL, Cypher, and vector ops. This forms a strong foundation for advanced use-cases like context engineering for AI (as in the REAgent project) and beyond, where an AI can reason over complex data and even update its knowledge on the fly in a controlled manner.

**Sources:**

* Apache AGE introduction and usage
* pgvector usage in PostgreSQL with Python
* Lark DSL parser design and testing principles
* Psycopg and SQLAlchemy for PostgreSQL in Python
* Click for CLI application structure and testing
* TriStore concept (structured + graph + vector) for context engineering

