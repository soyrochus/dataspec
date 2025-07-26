# Reagent Data Schema Definition Syntax (Draft)

**Version:** 1.0 **Status:** Draft **Purpose:** This document defines the syntax, conventions, and usage guidelines for authoring human-readable, hierarchical data model schemas in YAML for use within Reagent and related tooling.

## 1. Overview

The **Reagent Data Schema Definition Syntax** enables clear, concise modeling of structured data using YAML. It draws inspiration from OpenAPI’s schema object notation but introduces the reserved `<<root>>` identifier to explicitly mark the model entry point. Schemas are designed to be both machine- and human-readable, supporting recursive and nested object types.

## 2. Core Concepts

### 2.1 Root Definition

* The identifier `<<root>>` is **reserved** and denotes the root (entry point) of the schema.  
* The root is always an object; `type: object` is implied and MUST NOT be specified.  
* The fields of the root are defined as key-value pairs, where each value specifies the type and structure of the field.

### 2.2 Object Types

* Objects are defined by a `properties:` section, which lists field names and their types.  
* Each type (other than primitives or arrays) is defined at the top level with a unique name (e.g., `Project`, `Epic`).

### 2.3 Arrays

* Use `type: array` for any field that is a list.  
* The `items:` key specifies the type of each array element (either a primitive or a reference to another type using `$ref: '#/TypeName'`).

### 2.4 Primitives

* Supported primitive types: `string`, `integer`, `boolean`, etc.  
* Specify primitive type fields with `type: <primitive>`.

### 2.5 Optional properties

* Properties can be declared optional with the attribute “`optional`” of type `boolean` (`true` or `false`)  
* By default properties are mandatory (as if declared with `optional: false`).

### 2.5 Type References

* Use `$ref: '#/TypeName'` to refer to other defined types.  
* This supports recursive and nested structures (e.g., sub-tasks, sub-epics).

### 2.6 Documentation

* Use the `description:` key to document any field or type.  
* All documentation is optional but strongly encouraged.

## 3. Example Schema

```yaml
<<root>>:  
  projects:  
    type: array  
    items:  
      $ref: '#/Project'

Project:  
  properties:  
    name:  
      type: string  
      description: "Project name"  
    description:  
      type: string  
	optional: true  
      description: "Optional project overview"  
    epics:  
      type: array  
      description: "Top-level functional groupings"  
      items:  
        $ref: '#/Epic'

Epic:  
  properties:  
    id:  
      type: string  
    name:  
      type: string  
    description:  
      type: string  
    user_stories:  
      type: array  
      items:  
        $ref: '#/UserStory'  
    sub_epics:  
      type: array  
      items:  
        $ref: '#/Epic'

UserStory:  
  properties:  
    id:  
      type: string  
    name:  
      type: string  
    story:  
      type: string  
      description: "The user story statement"  
    priority:  
      type: string  
      description: "Priority level (e.g. high, medium, low)"  
    acceptance_criteria:  
      type: array  
      items:  
        type: string  
    tasks:  
      type: array  
      items:  
        $ref: '#/Task'

Task:  
  properties:  
    id:  
      type: string  
    description:  
      type: string  
    sub_tasks:  
      type: array  
      items:  
        $ref: '#/Task'
```

## 4. How-To Author a Reagent Data Schema

### 4.1 Start with the Root

* Begin your schema with the `<<root>>:` block.  
* Define the top-level fields and their types or references.

### 4.2 Define Each Type

* For each object referenced (e.g., `Project`, `Epic`), define a top-level block named exactly as referenced.  
* Under each, specify a `properties:` block mapping field names to their types, references, or array types.

### 4.3 Use Arrays and Recursion as Needed

* For list fields, use `type: array` and specify `items:`.  
* To enable recursive structures (like sub-tasks), reference the current type via `$ref`.

### 4.4 Add Documentation

* Use `description:` to clarify the meaning of types and fields.  
* Documenting schemas increases clarity and improves developer experience.

### 4.5 Supported Types

* **Primitives:** string, integer, boolean, number  
* **Arrays:** `type: array` with `items:` (which may be a primitive or `$ref`)  
* **Objects:** defined using `properties:`, referenced by `$ref`  
* **No other types are needed for most use cases.**

## 5. Example Data Instance

Given the above schema, an instance might look like:

```yaml
projects:  
  - name: "My Application"  
    description: "Internal modernization project"  
    epics:  
      - id: "EPIC-1"  
        name: "User Management"  
        user_stories:  
          - id: "US-001"  
            name: "Register new user"  
            story: "As a visitor, I want to register so that I can access member-only features."  
            priority: "high"  
            acceptance_criteria:  
              - "Validate email format"  
              - "Confirmation email sent"  
            tasks:  
              - id: "T1"  
                description: "Implement registration endpoint"  
                sub_tasks:  
                  - id: "T1.1"  
                    description: "Validate email"  
                    sub_tasks: []  
        sub_epics: []
```

## 6. Design Guidelines

* All types must be defined at the top level.  
* Always reference other types using `$ref: '#/TypeName'`.  
* Arrays must specify the type of their items.  
* The schema MUST have a single `<<root>>` entry point.  
* The root object must be fully defined by its properties; no circularity at the root.

## 7. Comparison to OpenAPI

* `<<root>>` replaces OpenAPI’s `components/schemas` entry point.  
* `type: object` is omitted where implied (root and property containers).  
* `$ref` syntax and other conventions are preserved for familiarity and extensibility.

## 8. Extensions

To support advanced validation, you may later extend this spec with:

* `enum`, `minLength`, `maxLength`, `pattern` for strings  
* `minimum`, `maximum` for numbers  
* `required` lists for required properties

## 9. Example recursive type: “Person” Schema

```yaml
<<root>>:  
  people:  
    type: array  
    items:  
      $ref: '#/Person'

Person:  
  properties:  
    name:  
      type: string  
    age:  
      type: integer  
    friends:  
      type: array  
      items:  
        $ref: '#/Person'
```

## **Appendix I** FAQ

**Q: Why not use OpenAPI’s full specification?** A: This syntax is lighter, more readable, and focused on data modeling, not HTTP or API operations.

**Q: Can I add examples or defaults?** A: Yes, you may add `example:` or `default:` fields for documentation, but these are not required by the base spec.

**Q: Can I validate data against these schemas?** A: Yes, with a parser or LLM-based tool. Conversion to JSON Schema is straightforward for enforcement.

## **Appendix II: Using JSON for Reagent Data Schema Definitions**

### **Overview**

While YAML is preferred for its readability, all Reagent schema and data definitions may be authored in **JSON**.

* The schema structure is identical—simply use JSON object/array/field notation instead of YAML.

* This allows compatibility with many editors, tools, and automation pipelines that work natively with JSON.

### **1. Writing a Reagent Schema in JSON**

**YAML Example:**

```yaml
<<root>>:  
  projects:  
    type: array  
    items:  
      $ref: '#/Project'  
Project:  
  properties:  
    name:  
      type: string  
    epics:  
      type: array  
      items:  
        $ref: '#/Epic'  
# etc.
```

**Equivalent JSON Example:**

```json
{  
  "<<root>>": {  
    "projects": {  
      "type": "array",  
      "items": { "$ref": "#/Project" }  
    }  
  },  
  "Project": {  
    "properties": {  
      "name": { "type": "string" },  
      "epics": {  
        "type": "array",  
        "items": { "$ref": "#/Epic" }  
      }  
    }  
  }  
  // etc.  
}
```

### **2. Writing Data Instances in JSON**

**YAML Data:**
```yaml
projects:  
  - name: "My Application"  
    epics:  
      - id: "EPIC-1"  
        name: "User Management"  
        user_stories: []
```

**Equivalent JSON Data:**

```json
{  
  "projects": [  
    {  
      "name": "My Application",  
      "epics": [  
        {  
          "id": "EPIC-1",  
          "name": "User Management",  
          "user_stories": []  
        }  
      ]  
    }  
  ]  
}
```

### **3. Interchangeability**

* **Validation tools** (like the Python script above) can accept either YAML or JSON files, as long as the structure is the same.

* You can freely convert between YAML and JSON using online tools, command-line utilities (`yq`, `jq`, etc.), or most programming languages.

### **4. Tips**

* Use JSON if integrating with systems or editors that do not natively support YAML.  
* For hand-written specs or collaborative editing, YAML is often easier to read and edit.  
* Always maintain the same top-level structure (including `<<root>>`) in both formats.

### **5. CLI Usage**

The sample `schema_val.py` will work for both YAML and JSON files, provided you use the appropriate file extension and content.

### **6. Example: Minimal Schema and Data in JSON**

**Schema (`schema.json`):**

```json
{  
  "<<root>>": {  
    "people": {  
      "type": "array",  
      "items": { "$ref": "#/Person" }  
    }  
  },  
  "Person": {  
    "properties": {  
      "name": { "type": "string" },  
      "age": { "type": "integer" }  
    }  
  }  
}
```

**Data (`data.json`):**

```json
{  
  "people": [  
    { "name": "Alice", "age": 33 },  
    { "name": "Bob", "age": 28 }  
  ]  
}
```

## **Appendix III:  Usage Examples

Validate YAML data and YAML schema:

```bash
python schema_val.py -d data.yml -s schema.yml
```

Validate JSON data and JSON schema:

```bash
python schema_val.py -d data.json -s schema.json
```

Mix YAML and JSON:

```bash
python schema_val.py -d data.json -s schema.yml
```

Force file format (e.g., file without extension):

```bash
python schema_val.py -d mydata -s myschema --data-format json --schema-format yaml  
```