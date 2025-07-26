# Reagent Data Schema Definition Syntax (Draft)

**Version:** 1.0 **Status:** Draft **Purpose:** This document defines the syntax, conventions, and usage guidelines for authoring human-readable, hierarchical data model schemas in YAML for use within Reagent and related tooling.

## 1. Overview

The **Reagent Data Schema Definition Syntax** enables clear, concise modeling of structured data using YAML. It draws inspiration from OpenAPI’s schema object notation but introduces the reser## 10. Example recursive type: "Person" Schemaed `<<root>>` identifier to explicitly mark the model entry point. Schemas are designed to be both machine- and human-readable, supporting recursive and nested object types.

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

### 2.6 Type References

* Use `$ref: '#/TypeName'` to refer to other defined types.  
* This supports recursive and nested structures (e.g., sub-tasks, sub-epics).

### 2.7 Documentation

* Use the `description:` key to document any field or type.  
* All documentation is optional but strongly encouraged.

## 3. Types Reference

This section provides a comprehensive reference of all supported types in the Reagent Data Schema Definition Syntax.

### 3.1 Primitive Types

#### 3.1.1 String Type
```yaml
field_name:
  type: string
  description: "Text data"
```

#### 3.1.2 Integer Type
```yaml
field_name:
  type: integer
  description: "Whole numbers (positive, negative, or zero)"
```

#### 3.1.3 Number Type
```yaml
field_name:
  type: number
  description: "Floating-point numbers"
```

#### 3.1.4 Boolean Type
```yaml
field_name:
  type: boolean
  description: "True or false values"
```

### 3.2 Collection Types

#### 3.2.1 Array Type
Arrays contain ordered lists of items of the same type.

```yaml
# Array of primitives
tags:
  type: array
  items:
    type: string

# Array of objects
users:
  type: array
  items:
    $ref: '#/User'

# Nested arrays (matrix)
matrix:
  type: array
  items:
    type: array
    items:
      type: number
```

#### 3.2.2 Map Type
Maps represent key-value collections (dictionaries/hash tables).

```yaml
# String-keyed map
config:
  type: map
  keys:
    type: string
  values:
    type: string

# Integer-keyed map
scores_by_year:
  type: map
  keys:
    type: integer
  values:
    type: number

# Map with complex values
departments:
  type: map
  keys:
    type: string
  values:
    type: array
    items:
      $ref: '#/Employee'

# Map with object values
locations:
  type: map
  keys:
    type: string
  values:
    $ref: '#/Address'
```

**Map Key Constraints:**
- Keys must be either `string` or `integer` type
- JSON serialization converts integer keys to strings automatically
- Maps do not allow additional properties beyond the defined value type

### 3.3 Object Types

#### 3.3.1 Named Object Types
Objects are defined at the top level with a unique name and referenced using `$ref`.

```yaml
User:
  properties:
    id:
      type: string
    name:
      type: string
    email:
      type: string
      optional: true
    preferences:
      type: map
      keys:
        type: string
      values:
        type: string
```

#### 3.3.2 Object References
Reference named types using the `$ref` syntax:

```yaml
<<root>>:
  current_user:
    $ref: '#/User'
  all_users:
    type: array
    items:
      $ref: '#/User'
```

### 3.4 Optional Fields

Any field can be marked as optional using the `optional: true` attribute:

```yaml
Person:
  properties:
    name:
      type: string
      # Required by default
    nickname:
      type: string
      optional: true
    age:
      type: integer
      optional: true
    address:
      $ref: '#/Address'
      optional: true
```

### 3.5 Recursive Types

Types can reference themselves to create recursive structures:

```yaml
TreeNode:
  properties:
    value:
      type: string
    children:
      type: array
      items:
        $ref: '#/TreeNode'
      optional: true

FileSystemItem:
  properties:
    name:
      type: string
    type:
      type: string
    children:
      type: array
      items:
        $ref: '#/FileSystemItem'
      optional: true
```

### 3.6 Complex Nested Structures

Combine all types to create sophisticated data models:

```yaml
<<root>>:
  organization:
    $ref: '#/Organization'

Organization:
  properties:
    name:
      type: string
    departments:
      type: map
      keys:
        type: string
      values:
        $ref: '#/Department'
    metadata:
      type: map
      keys:
        type: string
      values:
        type: string
      optional: true

Department:
  properties:
    name:
      type: string
    manager:
      $ref: '#/Employee'
    employees:
      type: array
      items:
        $ref: '#/Employee'
    budget_by_quarter:
      type: map
      keys:
        type: integer
      values:
        type: number

Employee:
  properties:
    id:
      type: string
    full_name:
      type: string
    skills:
      type: array
      items:
        type: string
    contact:
      $ref: '#/ContactInfo'
    reports:
      type: array
      items:
        $ref: '#/Employee'
      optional: true

ContactInfo:
  properties:
    email:
      type: string
    phone:
      type: string
      optional: true
    address:
      $ref: '#/Address'
      optional: true

Address:
  properties:
    street:
      type: string
    city:
      type: string
    postal_code:
      type: string
    country:
      type: string
    coordinates:
      type: array
      items:
        type: number
      optional: true
```

### 3.7 Type Constraints and Validation Rules

- **No Generic Objects:** The syntax does not support generic `type: object` as field types. Use named types and `$ref` instead.
- **Strict Type Checking:** All fields must have explicit type definitions.
- **No Null Types:** Null values are not supported as a type. Use `optional: true` for optional fields.
- **Key Type Restrictions:** Map keys are restricted to `string` and `integer` types only.
- **Required by Default:** All fields are required unless explicitly marked with `optional: true`.

## 4. Example Schema

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

## 5. How-To Author a Reagent Data Schema

### 5.1 Start with the Root

* Begin your schema with the `<<root>>:` block.  
* Define the top-level fields and their types or references.

### 5.2 Define Each Type

* For each object referenced (e.g., `Project`, `Epic`), define a top-level block named exactly as referenced.  
* Under each, specify a `properties:` block mapping field names to their types, references, or array types.

### 5.3 Use Arrays and Recursion as Needed

* For list fields, use `type: array` and specify `items:`.  
* To enable recursive structures (like sub-tasks), reference the current type via `$ref`.

### 5.4 Add Documentation

* Use `description:` to clarify the meaning of types and fields.  
* Documenting schemas increases clarity and improves developer experience.

### 5.5 Supported Types

* **Primitives:** string, integer, boolean, number  
* **Arrays:** `type: array` with `items:` (which may be a primitive or `$ref`)  
* **Objects:** defined using `properties:`, referenced by `$ref`  
* **No other types are needed for most use cases.**

## 6. Example Data Instance

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

## 7. Design Guidelines

* All types must be defined at the top level.  
* Always reference other types using `$ref: '#/TypeName'`.  
* Arrays must specify the type of their items.  
* The schema MUST have a single `<<root>>` entry point.  
* The root object must be fully defined by its properties; no circularity at the root.

## 8. Comparison to OpenAPI

* `<<root>>` replaces OpenAPI’s `components/schemas` entry point.  
* `type: object` is omitted where implied (root and property containers).  
* `$ref` syntax and other conventions are preserved for familiarity and extensibility.

## 9. Extensions

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

## Appendix III:  Usage Examples

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