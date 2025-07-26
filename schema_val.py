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
    Convert a reagent-style schema to JSON Schema,
    supporting 'optional: true' for properties (default: required).
    """
    def ref_to_json(ref):
        return ref.replace('#/', '#/definitions/')

    def rewrite_and_require(obj):
        if isinstance(obj, dict):
            out = {}
            for k, v in obj.items():
                if k == '$ref':
                    out[k] = ref_to_json(v)
                elif k == 'properties':
                    out[k] = {}
                    required = []
                    for prop, prop_def in v.items():
                        is_optional = (
                            isinstance(prop_def, dict) and prop_def.get("optional", False)
                        )
                        prop_def_noopt = dict(prop_def) if isinstance(prop_def, dict) else prop_def
                        if isinstance(prop_def_noopt, dict) and "optional" in prop_def_noopt:
                            del prop_def_noopt["optional"]
                        out[k][prop] = rewrite_and_require(prop_def_noopt)
                        if not is_optional:
                            required.append(prop)
                    if required:
                        out['required'] = required
                    out['additionalProperties'] = False
                else:
                    out[k] = rewrite_and_require(v)
            return out
        elif isinstance(obj, list):
            return [rewrite_and_require(i) for i in obj]
        else:
            return obj

    definitions = {k: v for k, v in reagent_schema.items() if k != '<<root>>'}
    definitions = {k: rewrite_and_require(v) for k, v in definitions.items()}
    root_props = reagent_schema['<<root>>']

    def root_required(props):
        req = []
        for k, v in props.items():
            if not (isinstance(v, dict) and v.get("optional", False)):
                req.append(k)
        return req

    json_schema = {
        "type": "object",
        "properties": rewrite_and_require(root_props),
        "definitions": definitions,
        "required": root_required(root_props),
        "additionalProperties": False
    }
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
