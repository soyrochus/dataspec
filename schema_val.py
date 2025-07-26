import sys
import os
import argparse
import yaml
import json
import jsonschema

def load_yaml_or_json(s):
    """
    Load YAML or JSON from a string.
    """
    try:
        return yaml.safe_load(s)
    except Exception:
        return json.loads(s)

def load_file(filename, force_format=None):
    """
    Load YAML or JSON file as Python object.
    Detects format by extension or optional force_format.
    """
    ext = os.path.splitext(filename)[1].lower()
    if force_format:
        fmt = force_format.lower()
    elif ext in ['.yaml', '.yml']:
        fmt = 'yaml'
    elif ext == '.json':
        fmt = 'json'
    else:
        raise Exception(f"Cannot infer file format from extension: {filename}")

    try:
        with open(filename, 'r') as f:
            if fmt == 'yaml':
                return yaml.safe_load(f)
            elif fmt == 'json':
                return json.load(f)
            else:
                raise Exception(f"Unknown format: {fmt}")
    except Exception as e:
        print(f"Error loading {filename}: {e}")
        sys.exit(2)

def is_json_schema(schema_obj):
    """
    Heuristically determine if schema_obj is already JSON Schema.
    Looks for '$schema' or typical JSON Schema keywords.
    """
    if isinstance(schema_obj, dict):
        if "$schema" in schema_obj:
            return True
        for k in ["type", "properties", "items", "required", "definitions", "$defs"]:
            if k in schema_obj:
                return True
    return False

def convert_reagent_to_jsonschema(reagent_schema):
    """
    Convert a strict Reagent schema to JSON Schema,
    supporting type: map (with keys/values) and banning generic object.
    """
    def error(msg):
        raise ValueError(f"Schema error: {msg}")

    def ref_to_json(ref):
        return ref.replace('#/', '#/definitions/')

    def is_named_type(name):
        return name in reagent_schema and "properties" in reagent_schema[name]

    def convert_field(obj, context=None):
        if not isinstance(obj, dict):
            return obj

        # Primitives, arrays, map, or $ref only!
        t = obj.get("type")
        if t == "map":
            keys = obj.get("keys")
            values = obj.get("values")
            if keys is None or values is None:
                error(f"type: map must have keys and values: {context}")
            if not isinstance(keys, dict) or not isinstance(values, dict):
                error(f"Map keys and values must be objects: {context}")
            
            # Type assertion for the linter
            assert isinstance(keys, dict)
            assert isinstance(values, dict)
            
            key_type = keys.get("type")
            if key_type not in ("string", "integer"):
                error(f"Map keys must be string or integer: {context}")
            
            # For JSON Schema, we need to handle integer keys specially
            # Since JSON object keys are always strings, we use pattern validation for integer keys
            if key_type == "integer":
                return {    
                    "type": "object",
                    "patternProperties": {
                        "^[0-9]+$": convert_field(values, context=f"{context} (map values)")
                    },
                    "additionalProperties": False
                }
            else:
                # String keys - use normal additionalProperties
                return {
                    "type": "object",
                    "additionalProperties": convert_field(values, context=f"{context} (map values)")
                }
        elif t == "array":
            items = obj.get("items")
            if not items:
                error(f"type: array must have items: {context}")
            return {
                "type": "array",
                "items": convert_field(items, context=f"{context} (array items)")
            }
        elif t in ("string", "integer", "number", "boolean"):
            r = {"type": t}
            for k in ("description",):  # preserve description, etc. if present
                if k in obj:
                    r[k] = obj[k]
            return r
        elif t == "object":
            # Only allowed for top-level named types with properties
            if context is not None:
                error("Generic 'object' as property is forbidden (use named types or map)")
            properties = obj.get("properties")
            if not properties:
                error("type: object must have properties for named types")
            # handled below in definitions
        elif "properties" in obj:
            # Should only happen for top-level named types
            error("Inline object definitions are not allowed. Use $ref to named types.")
        elif "$ref" in obj:
            return {"$ref": ref_to_json(obj["$ref"])}
        elif t == "null":
            error("Null type is not supported.")
        else:
            error(f"Unsupported or missing type in {obj} (context: {context})")
        return obj  # fallback (should never happen)

    # Convert definitions (top-level types only)
    definitions = {}
    for name, typ in reagent_schema.items():
        if name == "<<root>>":
            continue
        if not isinstance(typ, dict) or "properties" not in typ:
            error(f"Named type '{name}' must have properties")
        out = {"type": "object", "properties": {}, "additionalProperties": False}
        required = []
        for prop, propdef in typ["properties"].items():
            if propdef.get("optional", False):
                pass
            else:
                required.append(prop)
            pdef = dict(propdef)
            pdef.pop("optional", None)
            out["properties"][prop] = convert_field(pdef, context=f"{name}.{prop}")
        if required:
            out["required"] = required
        definitions[name] = out

    # Root schema
    root_props = reagent_schema["<<root>>"]
    
    # Handle required fields at root level (check for optional: true)
    root_required = []
    for prop, propdef in root_props.items():
        if not (isinstance(propdef, dict) and propdef.get("optional", False)):
            root_required.append(prop)
    
    json_schema = {
        "type": "object",
        "properties": {},
        "definitions": definitions,
        "additionalProperties": False,
        "required": root_required
    }
    for prop, propdef in root_props.items():
        pdef = dict(propdef)
        pdef.pop("optional", None)
        json_schema["properties"][prop] = convert_field(pdef, context=f"<<root>>.{prop}")

    return json_schema


def validate_data(data, schema, raise_error=True):
    """
    Validate a Python dict (data) against a schema (Reagent or JSON Schema).
    Returns True if valid, else returns (or raises) a human-readable error string.
    """
    if is_json_schema(schema):
        json_schema = schema
    else:
        json_schema = convert_reagent_to_jsonschema(schema)

    try:
        jsonschema.validate(instance=data, schema=json_schema)
        return True
    except jsonschema.ValidationError as e:
        msg = f"Validation failed: {e.message}\n"
        if e.absolute_path:
            msg += "Location: " + " -> ".join([str(p) for p in e.absolute_path]) + "\n"
        else:
            msg += "Location: (root)\n"
        if hasattr(e, 'instance'):
            snippet = json.dumps(e.instance, indent=2, ensure_ascii=False)
            if len(snippet) > 400:
                snippet = snippet[:400] + "... (truncated)"
            msg += "Data snippet: " + snippet
        if raise_error:
            raise ValueError(msg)
        else:
            return msg

# ------------------------------
# Command-line interface support
# ------------------------------
def main():
    parser = argparse.ArgumentParser(description="Validate YAML/JSON data against a Reagent or JSON Schema.")
    parser.add_argument("-d", "--data-file", required=True, help="Path to data file (.yml, .yaml, or .json)")
    parser.add_argument("-s", "--schema-file", required=True, help="Path to schema file (.yml, .yaml, or .json)")
    parser.add_argument("--data-format", choices=['yaml', 'json'], help="Force data format (yaml or json)")
    parser.add_argument("--schema-format", choices=['yaml', 'json'], help="Force schema format (yaml or json)")
    args = parser.parse_args()

    # Load files as Python objects
    data = load_file(args.data_file, force_format=args.data_format)
    schema_obj = load_file(args.schema_file, force_format=args.schema_format)

    try:
        result = validate_data(data, schema_obj, raise_error=False)
        if result is True:
            print("✅ Validation successful: Data matches the schema.")
            sys.exit(0)
        else:
            print("\n❌ Validation failed:\n")
            print(result)
            sys.exit(1)
    except Exception as ex:
        print(f"Unexpected error during validation: {ex}")
        sys.exit(3)

if __name__ == "__main__":
    main()
