from __future__ import annotations

import argparse
import sys
import yaml
from . import load_file, load_yaml_or_json, validate, search


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="dataspec", description="Validate and search data structures")
    sub = parser.add_subparsers(dest="command", required=True)

    val = sub.add_parser("validate", help="Validate data against a schema")
    val.add_argument("--data", required=True, help="Path to data file")
    val.add_argument("--schema", required=True, help="Path to schema file")
    val.add_argument("--data-format", choices=["yaml", "json"], help="Force data format")
    val.add_argument("--schema-format", choices=["yaml", "json"], help="Force schema format")

    sea = sub.add_parser("search", help="Search data using DataPath")
    sea.add_argument("--data", required=True, help="Path to data file")
    sea.add_argument("--path", required=True, help="DataPath expression")
    sea.add_argument("--data-format", choices=["yaml", "json"], help="Force data format")

    args = parser.parse_args(argv)

    if args.command == "validate":
        data = load_file(args.data, force_format=args.data_format)
        schema_obj = load_file(args.schema, force_format=args.schema_format)
        try:
            result = validate(data, schema_obj, raise_error=False)
            if result is True:
                print("✅ Validation successful: Data matches the schema.")
                return
            print("\n❌ Validation failed:\n")
            print(result)
            sys.exit(1)
        except Exception as ex:
            print(f"Unexpected error during validation: {ex}")
            sys.exit(3)
    elif args.command == "search":
        data = load_file(args.data, force_format=args.data_format)
        try:
            value = search(data, args.path)
            if isinstance(value, (dict, list)):
                print(yaml.safe_dump(value, sort_keys=False).rstrip())
            else:
                print(value)
        except Exception as ex:
            print(f"Error: {ex}")
            sys.exit(1)


if __name__ == "__main__":
    main()
