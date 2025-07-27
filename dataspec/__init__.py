# Dataspec library: validation and DataPath search
from __future__ import annotations

import os
import json
import yaml
import jsonschema
from typing import Any

__all__ = [
    "load_yaml_or_json",
    "load_file",
    "convert_yaml_to_jsonschema",
    "validate",
    "resolve_datapath",
    "search",
]


def load_yaml_or_json(s: str) -> Any:
    """Load YAML or JSON from a string."""
    try:
        return yaml.safe_load(s)
    except Exception:
        return json.loads(s)


def load_file(filename: str, force_format: str | None = None) -> Any:
    """Load YAML or JSON file as a Python object."""
    ext = os.path.splitext(filename)[1].lower()
    if force_format:
        fmt = force_format.lower()
    elif ext in {".yaml", ".yml"}:
        fmt = "yaml"
    elif ext == ".json":
        fmt = "json"
    else:
        raise ValueError(f"Cannot infer file format from extension: {filename}")
    with open(filename, "r") as f:
        if fmt == "yaml":
            return yaml.safe_load(f)
        if fmt == "json":
            return json.load(f)
    raise ValueError(f"Unknown format: {fmt}")


def is_json_schema(schema_obj: Any) -> bool:
    """Heuristically determine if the object already looks like JSON Schema."""
    if isinstance(schema_obj, dict):
        if "$schema" in schema_obj:
            return True
        for k in ["type", "properties", "items", "required", "definitions", "$defs"]:
            if k in schema_obj:
                return True
    return False


def convert_yaml_to_jsonschema(yaml_schema: dict[str, Any]) -> dict[str, Any]:
    """Convert a Yaml schema to JSON Schema."""

    def error(msg: str) -> None:
        raise ValueError(f"Schema error: {msg}")

    def ref_to_json(ref: str) -> str:
        return ref.replace("#/", "#/definitions/")

    def convert_field(obj: Any, context: str | None = None) -> Any:
        if not isinstance(obj, dict):
            return obj
        t = obj.get("type")
        if t == "map":
            keys = obj.get("keys")
            values = obj.get("values")
            if keys is None or values is None:
                error(f"type: map must have keys and values: {context}")
            assert isinstance(keys, dict)
            assert isinstance(values, dict)
            key_type = keys.get("type")
            if key_type not in ("string", "integer"):
                error(f"Map keys must be string or integer: {context}")
            if key_type == "integer":
                return {
                    "type": "object",
                    "patternProperties": {
                        "^[0-9]+$": convert_field(values, context=f"{context} (map values)")
                    },
                    "additionalProperties": False,
                }
            return {
                "type": "object",
                "additionalProperties": convert_field(values, context=f"{context} (map values)")
            }
        if t == "array":
            items = obj.get("items")
            if not items:
                error(f"type: array must have items: {context}")
            return {"type": "array", "items": convert_field(items, context=f"{context} (array items)")}
        if t in ("string", "integer", "number", "boolean"):
            r = {"type": t}
            if "description" in obj:
                r["description"] = obj["description"]
            return r
        if t == "object":
            if context is not None:
                error("Generic 'object' as property is forbidden (use named types or map)")
            properties = obj.get("properties")
            if not properties:
                error("type: object must have properties for named types")
        elif "properties" in obj:
            error("Inline object definitions are not allowed. Use $ref to named types.")
        elif "$ref" in obj:
            return {"$ref": ref_to_json(obj["$ref"])}
        elif t == "null":
            error("Null type is not supported.")
        else:
            error(f"Unsupported or missing type in {obj} (context: {context})")
        return obj

    definitions: dict[str, Any] = {}
    for name, typ in yaml_schema.items():
        if name == "<<root>>":
            continue
        if not isinstance(typ, dict) or "properties" not in typ:
            error(f"Named type '{name}' must have properties")
        out: dict[str, Any] = {"type": "object", "properties": {}, "additionalProperties": False}
        required: list[str] = []
        for prop, propdef in typ["properties"].items():
            if not propdef.get("optional", False):
                required.append(prop)
            pdef = dict(propdef)
            pdef.pop("optional", None)
            out["properties"][prop] = convert_field(pdef, context=f"{name}.{prop}")
        if required:
            out["required"] = required
        definitions[name] = out

    root_props = yaml_schema["<<root>>"]
    root_required: list[str] = []
    for prop, propdef in root_props.items():
        if not (isinstance(propdef, dict) and propdef.get("optional", False)):
            root_required.append(prop)

    json_schema = {
        "type": "object",
        "properties": {},
        "definitions": definitions,
        "additionalProperties": False,
        "required": root_required,
    }
    for prop, propdef in root_props.items():
        pdef = dict(propdef)
        pdef.pop("optional", None)
        json_schema["properties"][prop] = convert_field(pdef, context=f"<<root>>.{prop}")
    return json_schema


def validate(data: Any, schema: Any, *, raise_error: bool = True) -> bool | str:
    """Validate data against schema. Returns True or error string."""
    json_schema = schema if is_json_schema(schema) else convert_yaml_to_jsonschema(schema)
    try:
        jsonschema.validate(instance=data, schema=json_schema)
        return True
    except jsonschema.ValidationError as e:
        msg = f"Validation failed: {e.message}\n"
        if e.absolute_path:
            msg += "Location: " + " -> ".join(str(p) for p in e.absolute_path) + "\n"
        else:
            msg += "Location: (root)\n"
        if hasattr(e, "instance"):
            snippet = json.dumps(e.instance, indent=2, ensure_ascii=False)
            if len(snippet) > 400:
                snippet = snippet[:400] + "... (truncated)"
            msg += "Data snippet: " + snippet
        if raise_error:
            raise ValueError(msg)
        return msg


def _split_segments(path: str) -> list[str]:
    segments: list[str] = []
    buf = ""
    level = 0
    for ch in path:
        if ch in "./" and level == 0:
            if buf:
                segments.append(buf)
                buf = ""
            continue
        buf += ch
        if ch == "[":
            level += 1
        elif ch == "]":
            level -= 1
    if buf:
        segments.append(buf)
    return segments


def _parse_segment(seg: str) -> tuple[str | None, list[str]]:
    name = None
    selectors: list[str] = []
    i = 0
    while i < len(seg) and seg[i] != "[":
        name = seg[:i + 1]
        i += 1
    if name is None:
        name = ""
    rest = seg[len(name):]
    while rest:
        if not rest.startswith("["):
            raise ValueError(f"Malformed segment: {seg}")
        j = rest.find("]")
        if j == -1:
            raise ValueError(f"Malformed segment: {seg}")
        selectors.append(rest[1:j])
        rest = rest[j + 1:]
    return name, selectors


def resolve_datapath(data: Any, path: str) -> Any:
    """Resolve a DataPath expression against data."""
    current = data
    for raw_seg in _split_segments(path):
        name, selectors = _parse_segment(raw_seg)
        if name:
            if isinstance(current, dict) and name in current:
                current = current[name]
            else:
                raise KeyError(name)
        for sel in selectors:
            if sel.isdigit() or (sel.startswith("-") and sel[1:].isdigit()):
                idx = int(sel)
                if isinstance(current, list):
                    current = current[idx]
                else:
                    raise IndexError(f"Index {idx} on non-list")
            elif sel.startswith("\"") or sel.startswith("'"):
                key = yaml.safe_load(sel)
                if isinstance(current, dict) and key in current:
                    current = current[key]
                else:
                    raise KeyError(key)
            elif "=" in sel:
                field, value = sel.split("=", 1)
                if value.startswith("\"") or value.startswith("'"):
                    value = yaml.safe_load(value)
                elif value.isdigit() or (value.startswith("-") and value[1:].isdigit()):
                    value = int(value)
                for item in current:
                    if isinstance(item, dict) and item.get(field) == value:
                        current = item
                        break
                else:
                    raise KeyError(f"No element with {field}={value}")
            else:
                key = sel
                if isinstance(current, dict) and key in current:
                    current = current[key]
                else:
                    raise KeyError(key)
    return current


def search(data: Any, path: str) -> Any:
    """Public wrapper around :func:`resolve_datapath`."""
    return resolve_datapath(data, path)

