import pytest
from schema_val import validate_data, load_yaml_or_json

# --- EXAMPLE DATA/SCHMEA AS STRINGS ---

DATA_YAML = """
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
"""

SCHEMA_YAML = """
<<root>>:
  projects:
    type: array
    items:
      $ref: '#/Project'

Project:
  properties:
    name:
      type: string
    description:
      type: string
      optional: true
    epics:
      type: array
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
      optional: true
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
    priority:
      type: string
      optional: true
    acceptance_criteria:
      type: array
      items:
        type: string
      optional: true
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
"""

DATA_JSON = {
    "projects": [
        {
            "name": "My Application",
            "description": "Internal modernization project",
            "epics": [
                {
                    "id": "EPIC-1",
                    "name": "User Management",
                    "user_stories": [
                        {
                            "id": "US-001",
                            "name": "Register new user",
                            "story": "As a visitor, I want to register so that I can access member-only features.",
                            "priority": "high",
                            "acceptance_criteria": [
                                "Validate email format",
                                "Confirmation email sent"
                            ],
                            "tasks": [
                                {
                                    "id": "T1",
                                    "description": "Implement registration endpoint",
                                    "sub_tasks": [
                                        {
                                            "id": "T1.1",
                                            "description": "Validate email",
                                            "sub_tasks": []
                                        }
                                    ]
                                }
                            ]
                        }
                    ],
                    "sub_epics": []
                }
            ]
        }
    ]
}

SCHEMA_JSON = {
    "<<root>>": {
        "projects": {
            "type": "array",
            "items": { "$ref": "#/Project" }
        }
    },
    "Project": {
        "properties": {
            "name": { "type": "string" },
            "description": { "type": "string", "optional": True },
            "epics": {
                "type": "array",
                "items": { "$ref": "#/Epic" }
            }
        }
    },
    "Epic": {
        "properties": {
            "id": { "type": "string" },
            "name": { "type": "string" },
            "description": { "type": "string", "optional": True },
            "user_stories": {
                "type": "array",
                "items": { "$ref": "#/UserStory" }
            },
            "sub_epics": {
                "type": "array",
                "items": { "$ref": "#/Epic" }
            }
        }
    },
    "UserStory": {
        "properties": {
            "id": { "type": "string" },
            "name": { "type": "string" },
            "story": { "type": "string" },
            "priority": { "type": "string", "optional": True },
            "acceptance_criteria": {
                "type": "array",
                "items": { "type": "string" },
                "optional": True
            },
            "tasks": {
                "type": "array",
                "items": { "$ref": "#/Task" }
            }
        }
    },
    "Task": {
        "properties": {
            "id": { "type": "string" },
            "description": { "type": "string" },
            "sub_tasks": {
                "type": "array",
                "items": { "$ref": "#/Task" }
            }
        }
    }
}

# --- TESTS ---

def test_valid_yaml_files():
    data = load_yaml_or_json(DATA_YAML)
    schema = load_yaml_or_json(SCHEMA_YAML)
    assert validate_data(data, schema, raise_error=False) is True

def test_valid_json_dicts():
    assert validate_data(DATA_JSON, SCHEMA_JSON, raise_error=False) is True

def test_valid_yaml_data_json_schema():
    data = load_yaml_or_json(DATA_YAML)
    assert validate_data(data, SCHEMA_JSON, raise_error=False) is True

def test_valid_json_data_yaml_schema():
    schema = load_yaml_or_json(SCHEMA_YAML)
    assert validate_data(DATA_JSON, schema, raise_error=False) is True

def test_invalid_missing_required():
    # Remove a required property (e.g., name) from Project
    invalid = {
        "projects": [
            {
                # "name": "My Application",  # Missing!
                "description": "Internal modernization project",
                "epics": []
            }
        ]
    }
    result = validate_data(invalid, SCHEMA_JSON, raise_error=False)
    assert result is not True
    assert "name" in result

def test_invalid_type():
    # Make name (should be string) an integer
    invalid = {
        "projects": [
            {
                "name": 1234,
                "description": "Internal modernization project",
                "epics": []
            }
        ]
    }
    result = validate_data(invalid, SCHEMA_JSON, raise_error=False)
    assert result is not True
    assert "is not of type 'string'" in result

def test_optional_fields():
    # Omit an optional property (e.g., description)
    valid = {
        "projects": [
            {
                "name": "My Application",
                # "description": "Internal modernization project",  # Omitted!
                "epics": []
            }
        ]
    }
    assert validate_data(valid, SCHEMA_JSON, raise_error=False) is True

def test_additional_property():
    # Add a property not in schema
    invalid = {
        "projects": [
            {
                "name": "My Application",
                "epics": [],
                "extra": 123
            }
        ]
    }
    result = validate_data(invalid, SCHEMA_JSON, raise_error=False)
    assert result is not True
    assert "Additional properties are not allowed" in result

