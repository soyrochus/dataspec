Got it. I’ll now generate a single, detailed prompt you can copy-paste into an advanced AI code generation agent like Claude or Codex to begin implementation of the DSL and runtime.


# Test-Driven Implementation Plan for a PostgreSQL “TriStore” DSL and Runtime

## Overview and Objectives

* **Goal:** Implement a Python 3.10+ DSL (domain-specific language) and runtime to interact with a PostgreSQL-based “TriStore”. The TriStore combines three data facets in one Postgres instance:

  * **Structured data:** traditional relational entities and attributes (tables/columns).
  * **Graph data:** graph relationships using the Apache AGE extension (which enables Cypher queries in Postgres).
  * **Vector embeddings:** similarity search using the pgvector extension in Postgres.
* **Key Objectives:**

  1. **Open-Source Stack:** Use only open-source, industry-standard libraries (e.g. Lark for parsing, Psycopg3 for database access, Click for CLI, etc.).
  2. **Two-Phase Delivery:**

     * *Phase 1:* Core schema definition and read-only query capabilities.
     * *Phase 2:* Data modification (create/update) and vector similarity search features.
  3. **CLI Access:** Provide a command-line interface for interactive use and scripting (the tool will be invoked as a console script, e.g. `tristore-cli`).
  4. **LLM-Friendly:** Design the DSL so that it can be used not just by developers but also by LLM agents (AI agents that translate natural language to DSL queries).
  5. **Test-Driven Development:** Adopt TDD for each milestone – write tests for each feature **before** implementing it. This ensures reliability and verifiability from the start.

By following this plan, you will progressively build a robust DSL and runtime that can be safely used by both humans and AI agents to query and manipulate the TriStore.

## Architecture and Module Breakdown

The project is structured into modular components, each responsible for a specific aspect of the DSL or runtime:

* **DSL Parser Module:** Use **Lark** to define an EBNF grammar and parse DSL statements into an Abstract Syntax Tree (AST) or intermediate representation.

  * The grammar will cover DSL statements for schema definitions (entities and relationships), query patterns (graph traversals, selection criteria), and later data manipulation (create/update statements).
  * Lark is chosen for its easy grammar definition and built-in lexing/parsing capabilities. The parser will output AST node objects corresponding to each DSL construct (e.g. an `EntityDef` node for an entity definition).

* **AST and Semantic Model:** Define Python classes to represent AST nodes (e.g. `EntityDef`, `RelationDef`, `QueryStmt`, `CreateOp`, `UpdateOp`, etc.) and perform semantic validation.

  * This layer checks that parsed statements make sense: for example, if a query refers to an entity or relationship, those must have been defined; avoid duplicate definitions, etc.
  * The AST nodes will likely have methods or handlers to facilitate execution (for instance, a `QueryStmt` AST node might have a method to generate the corresponding SQL/Cypher query for execution).

* **Runtime Engine:** This component takes AST nodes and executes them against the PostgreSQL TriStore database. It comprises several sub-components:

  * **Schema Manager:** Maintains metadata about defined entities and relationships. In Phase 1, this can be in-memory (e.g. dictionaries mapping entity names to their properties, and relationship names to their source/target entity types). It should support introspection commands (like a DSL command to list all entities or relations). Later, this might persist to the database or be able to reflect existing database schema.
  * **Query Executor:** Handles read-only queries. It translates a DSL query AST into actual database queries. For graph traversals, this means translating into an Apache AGE Cypher query (for example, using `SELECT * FROM cypher('graph_name', $$ MATCH (p:Person)-[:FRIEND]->(f:Person) RETURN f $$)`). For relational data lookup, it could generate standard SQL `SELECT` queries. The Query Executor uses **Psycopg3** to execute the generated SQL/Cypher against PostgreSQL and fetch results.
  * **Data Manipulation Handler:** (Planned for Phase 2) Handles create/update operations. It will translate DSL commands for inserting or updating data into SQL/Cypher. For instance, a DSL command to create a new entity node would result in an `INSERT` or an AGE Cypher `CREATE` query; updating a property might use a Cypher `SET` clause on a node or an `UPDATE` SQL statement for a relational table.
  * **Vector Search Handler:** (Planned for Phase 2) Integrates vector similarity queries via pgvector. For example, if the DSL has a command like `FIND NEAREST <vector> IN <Entity> LIMIT 5`, this component would translate it to a SQL query using pgvector’s `<->` or `<=>` operators for cosine or Euclidean distance, or using an index-backed similarity search. It may require maintaining a special table or extending entity tables with vector columns for embeddings.

* **Database Connector:** Encapsulates the connection to the PostgreSQL database using **psycopg3** (the modern Psycopg, which supports async operations and is suited for Python 3.10+). This will manage connecting to the database, executing queries, handling transactions, etc. By abstracting this, the rest of the system can call high-level methods (like `db.execute_query(sql)`) without worrying about connection details. We will likely use a single connection or a pool during CLI use and tests. Ensure the connector can work in synchronous mode (for simplicity in CLI and tests) and possibly asynchronous if needed later.

* **CLI Interface Module:** Provide a user-facing command-line tool (using **Click** library for argument parsing and commands). The CLI will allow users to enter DSL commands interactively or run a script of DSL commands. For example, a user can type `tristore-cli` to enter an interactive prompt or do `tristore-cli run script.dsl`. The CLI will utilize the parser and runtime engine under the hood: it will parse input commands, execute them via the runtime, and display results or errors. This CLI should also be designed such that an LLM agent could invoke the same functionalities by calling the underlying Python API (so the core functionality is not tied only to the console I/O).

* **Testing Suite:** A comprehensive set of tests (using **pytest**) will be developed alongside the code (TDD). Organize tests by module/milestone. For Phase 1, tests will cover parsing of DSL statements, schema manager behavior, query execution logic (which might be mostly stubbed or simple until Phase 2 data is available), and CLI interactions. Integration tests will be needed that run against an actual PostgreSQL instance with AGE and pgvector enabled. (Using a Dockerized Postgres 16 with those extensions is recommended for both local development and CI.)

Each component above will interact through well-defined interfaces. For example, the CLI will take user input and simply call the parser and runtime engine; the parser produces an AST which is passed to the runtime engine; the runtime engine uses the database connector to execute queries. This modular design will make the system easier to test, maintain, and extend.

## Phase 1: Core Schema Definition & Read-Only Queries

Phase 1 establishes the fundamental capabilities of the DSL: the ability to define a schema (entities and relationships) and to perform read-only queries (particularly graph traversals or simple selections) based on that schema. Phase 1 will *not* include data mutation or vector search yet – those will come in Phase 2. We will proceed with a test-driven approach, implementing the following milestones one by one:

### Milestone 1: Project Setup & Infrastructure

**Objective:** Set up the basic project structure, ensure the environment is ready (including database with required extensions), and implement a trivial CLI command to verify everything is wired up.

* **Project Initialization:** Create a new Python project (e.g. `tristore_dsl` as the main package). Set up a `pyproject.toml` or `setup.py` (consider using Poetry or pip-tools for environment management). Create the core package directory (`tristore_dsl/`) and an empty tests directory (`tests/`). Ensure the package is installable (you might create a version `0.1.0` for example).

* **Version Control and CI:** Initialize a Git repository. Optionally set up continuous integration (for example, using GitHub Actions) to run tests on push. In CI, configure a service/container for PostgreSQL 16 with Apache AGE and pgvector extensions enabled (this might involve using a Docker image or Docker Compose file in the repo). The CI should run `pytest` to execute the test suite. Verify that the CI can connect to the database (you might write a dummy test that connects and executes `SELECT 1`).

* **Database Environment:** Provide a **Docker Compose** configuration (for local development and testing) that starts a PostgreSQL 16 server with the required extensions (Apache AGE, pgvector). For example, use the official Postgres image and run SQL commands to create the extensions on startup. Ensure that local tests can use this database (you can set connection parameters as environment variables or defaults, e.g. `POSTGRES_URL=...`).

* **CLI Scaffolding:** Implement a minimal CLI using **Click**. For now, just implement a `--version` option and a base command group. For example, running `tristore-cli --version` should print the tool’s version. The CLI entry point should be configured in `pyproject.toml` or `setup.cfg` so that installing the package provides the `tristore-cli` command. Use Click’s `group()` and `command()` decorators to set up the structure.

* **Smoke Tests:** Write initial tests to validate the setup:

  * A test that the CLI `--version` returns the expected version string. Use Click’s testing utility `CliRunner` to invoke the CLI in tests.
  * A test that establishes a connection to the PostgreSQL test database (using the Database Connector). For example, use psycopg to execute a simple query (`SELECT 1`) and assert that it returns the expected result.
  * A test that the core package is importable (e.g., `import tristore_dsl` doesn’t raise errors). This ensures the project structure is correct.

By completing Milestone 1, we will have a functioning project scaffold: the test framework is in place, the CLI can be invoked (at least for a version check), and the database environment is confirmed accessible. This provides a foundation to start building actual DSL features.

### Milestone 2: Entity and Relationship Definition DSL

**Objective:** Enable the DSL to define schema elements (entity types and relationship types) and store these definitions in the system’s schema manager. We will implement parsing of `DEFINE ENTITY` and `DEFINE RELATION` statements, create the AST representations, and update the Schema Manager accordingly. This milestone is purely about **schema definition** and does not yet query or modify actual data rows in the database.

* **DSL Grammar for Definitions:** Using Lark, define grammar rules for schema definition statements:

  * Syntax for defining an entity type, for example:

    ```
    DEFINE ENTITY <EntityName> ( <prop1> <Type1>, <prop2> <Type2>, ... );
    ```

    e.g. `DEFINE ENTITY Person (name TEXT, age INT);`
    This means an entity type "Person" with properties `name` (text) and `age` (integer).
  * Syntax for defining a relationship type, for example:

    ```
    DEFINE RELATION <RelationName> ( <EntityTypeA> -> <EntityTypeB> );
    ```

    e.g. `DEFINE RELATION Friend (Person -> Person);` for a relationship "Friend" between two Person entities (likely implying a symmetric "friends with" relationship, or directed if order matters).
  * The grammar in Lark will likely have non-terminals like `entity_def` and `relation_def`, and tokens for keywords `DEFINE`, `ENTITY`, `RELATION`, arrow `->`, parentheses, identifiers (for names), types, and punctuation. Define these productions in an EBNF style within a grammar string for Lark.

* **Parsing and AST Construction:** Implement the Lark parser and a transformer or post-processing step to convert the parse tree into AST node objects.

  * Define Python classes for AST nodes, e.g. an `EntityDef` class with attributes like `name` (string) and `properties` (list of (name, type) pairs), and a `RelationDef` class with attributes like `name`, `source_entity`, `target_entity`.
  * When the parser recognizes a `DEFINE ENTITY` statement, it should produce an `EntityDef` instance. Similarly, a `DEFINE RELATION` yields a `RelationDef` instance.
  * Include basic semantic validation during this stage or in the next step: for example, if the grammar allows it, ensure that an entity or relation name is a valid identifier (no special characters, not a SQL reserved word perhaps), and that property types are recognized types (you might allow types like TEXT, INT, FLOAT, etc., mapping to PostgreSQL types).

* **Schema Manager (In-Memory):** Implement a `SchemaManager` component in the runtime to store the defined schema. In Phase 1, this can simply maintain Python dictionaries or maps:

  * `entities`: map entity name -> details (like a dict of property names and types).
  * `relations`: map relation name -> (source\_entity, target\_entity).
  * Provide methods like `add_entity(EntityDef)` and `add_relation(RelationDef)` which will register these definitions. These methods should perform checks: e.g., if an entity name or relation name is already defined, raise an error to prevent duplicates; if adding a relation, verify that the referenced source/target entity types have been defined previously (or at least exist in the entities map).
  * (For now, we do not actually create any database tables or graph schemas when an entity or relation is defined, but we **could** choose to create a placeholder in the database. For example, with Apache AGE, you don’t need to pre-create labels for nodes and edges – they are created when first used. But we might ensure the graph itself exists by calling a setup like `SELECT create_graph('main')` once. We can handle that either here or at runtime initialization.)

* **Testing (TDD approach):** Write tests for the above before full implementation, then implement until tests pass:

  * **Parser Tests:** Given an input DSL string like `"DEFINE ENTITY Person (name TEXT, age INT);"`, after parsing, the result should be an `EntityDef` object with `name="Person"` and a property list containing `("name","TEXT"), ("age","INT")`. Similarly, test that `"DEFINE RELATION Friend (Person -> Person);"` produces a `RelationDef` with `name="Friend"`, `source_entity="Person"`, `target_entity="Person"`.
  * **SchemaManager Tests:** After parsing a definition, apply it to the SchemaManager (e.g., call `SchemaManager.add_entity(entity_def)`). Then verify that the SchemaManager indeed stores the entity. For example, `SchemaManager.get_entity("Person")` returns the metadata with the expected properties. Do the same for relations.
  * **Error Conditions:** Test that defining a duplicate entity name raises an appropriate exception or error. Test that defining a relation with an undefined entity type is rejected (e.g., `DEFINE RELATION Foo (X -> Y)` when no entity X or Y exists). The parser might not catch this (since it only checks syntax), but the semantic validation in SchemaManager or a semantic analysis phase should catch it. Ensure the system provides a clear error message for these cases.

* **Implementation:** Write the minimal code to make the above tests pass:

  * Create the Lark grammar and parser. Use Lark’s `LALR` or `Earley` parser as needed (likely LALR since the grammar should be unambiguous). Implement either a Lark Transformer or manually walk the parse tree to construct AST node instances.
  * Implement the AST node classes (`EntityDef`, `RelationDef`, etc.) perhaps in a module like `tristore_dsl.ast`. These can be simple data classes (could even use `@dataclass` for convenience).
  * Implement the SchemaManager in `tristore_dsl.runtime.schema` (for example). This could be a singleton or a class that is instantiated as part of a runtime context. A simple approach is to use a module-level singleton for now, or a class with classmethods for global state, since our CLI will be single-user. Ensure thread-safety is not a concern in this phase (single-threaded CLI usage).
  * Integrate the parser with the SchemaManager: the CLI (or a higher-level command handler) should be able to take a DSL string, parse it to AST, recognize that it’s a definition statement, and then call SchemaManager to register it. For now, focus on the backend logic (parsing and registration) and less on the CLI input loop (that can be refined later).

* **Graph Setup (optional):** As part of this milestone (or the next), you may execute an initialization query to ensure the Apache AGE graph is created. For example, run `SELECT create_graph('main');` once so that subsequent Cypher queries run in the context of this graph. This could be done either in the SchemaManager when the first entity is defined, or as an explicit initialization step in the CLI or a setup function. Add a note to handle this in Phase 1 to avoid missing it when queries are executed.

By the end of Milestone 2, the system can parse DSL commands that define entities and relationships and store this schema information in memory. We will have verified via tests that the parser works for valid inputs and that the SchemaManager correctly registers the definitions (and prevents invalid ones). At this stage, no actual data is stored in the PostgreSQL database yet (and no tables/nodes are created by the DSL definitions, aside from setting up the graph context if needed). The groundwork is laid to proceed to querying capabilities in the next milestones.


* Instructions:

- Rename the current dataspec directory to "old_dataspect" 
- Do NOT focus in any way on creation of Dockerfile etc as these are already implemented. Assume the database (the Tristore) works
- Focus on having a working DSL with workable and testable use cases
- create the database sctipts needed to do the tests 
- The DSL shouyld be usable with Pytest test cases and the CLI


