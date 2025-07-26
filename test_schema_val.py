import pytest
import tempfile
import os
from schema_val import validate_data, load_yaml_or_json, load_file

# Test data for all supported types according to the Yaml Schema Definition Syntax
COMPREHENSIVE_SCHEMA_YAML = """
<<root>>:
  test_data:
    $ref: '#/TestData'

TestData:
  properties:
    # Primitive types
    name:
      type: string
    age:
      type: integer
    salary:
      type: number
    is_active:
      type: boolean
    
    # Optional primitive
    nickname:
      type: string
      optional: true
    
    # Arrays of primitives
    tags:
      type: array
      items:
        type: string
    scores:
      type: array
      items:
        type: integer
    
    # Nested arrays (array of arrays)
    matrix:
      type: array
      items:
        type: array
        items:
          type: number
    
    # Maps/Dictionaries
    config:
      type: map
      keys:
        type: string
      values:
        type: string
    
    scores_by_year:
      type: map
      keys:
        type: integer
      values:
        type: number
    
    # Map with complex values (array)
    lists_by_category:
      type: map
      keys:
        type: string
      values:
        type: array
        items:
          type: string
    
    # Map with object reference values
    people_by_id:
      type: map
      keys:
        type: string
      values:
        $ref: '#/Person'
    
    # Array of objects
    team_members:
      type: array
      items:
        $ref: '#/Person'
    
    # Nested object
    address:
      $ref: '#/Address'
    
    # Optional complex types
    secondary_address:
      $ref: '#/Address'
      optional: true

Person:
  properties:
    id:
      type: string
    full_name:
      type: string
    contact:
      $ref: '#/ContactInfo'
    skills:
      type: array
      items:
        type: string
    metadata:
      type: map
      keys:
        type: string
      values:
        type: string
      optional: true

ContactInfo:
  properties:
    email:
      type: string
    phone:
      type: string
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
"""

VALID_DATA_YAML = """
test_data:
  name: "John Doe"
  age: 30
  salary: 75000.50
  is_active: true
  nickname: "Johnny"
  tags: ["developer", "python", "yaml"]
  scores: [85, 92, 78]
  matrix:
    - [1.0, 2.0, 3.0]
    - [4.0, 5.0, 6.0]
  config:
    theme: "dark"
    language: "en"
  scores_by_year:
    "2022": 88.5
    "2023": 92.0
  lists_by_category:
    programming: ["python", "javascript"]
    databases: ["postgresql", "mongodb"]
  people_by_id:
    "emp001":
      id: "emp001"
      full_name: "Alice Smith"
      contact:
        email: "alice@example.com"
        phone: "+1-555-0101"
      skills: ["python", "docker"]
    "emp002":
      id: "emp002"
      full_name: "Bob Johnson"
      contact:
        email: "bob@example.com"
      skills: ["javascript", "react"]
  team_members:
    - id: "tm001"
      full_name: "Charlie Brown"
      contact:
        email: "charlie@example.com"
      skills: ["go", "kubernetes"]
    - id: "tm002"
      full_name: "Diana Prince"
      contact:
        email: "diana@example.com"
        phone: "+1-555-0202"
      skills: ["rust", "webassembly"]
      metadata:
        department: "engineering"
        level: "senior"
  address:
    street: "123 Main St"
    city: "Anytown"
    postal_code: "12345"
    country: "USA"
    coordinates: [40.7128, -74.0060]
"""

# JSON equivalents for testing
COMPREHENSIVE_SCHEMA_JSON = {
    "<<root>>": {
        "test_data": {"$ref": "#/TestData"}
    },
    "TestData": {
        "properties": {
            "name": {"type": "string"},
            "age": {"type": "integer"},
            "salary": {"type": "number"},
            "is_active": {"type": "boolean"},
            "nickname": {"type": "string", "optional": True},
            "tags": {"type": "array", "items": {"type": "string"}},
            "scores": {"type": "array", "items": {"type": "integer"}},
            "matrix": {
                "type": "array",
                "items": {
                    "type": "array",
                    "items": {"type": "number"}
                }
            },
            "config": {
                "type": "map",
                "keys": {"type": "string"},
                "values": {"type": "string"}
            },
            "scores_by_year": {
                "type": "map",
                "keys": {"type": "integer"},
                "values": {"type": "number"}
            },
            "lists_by_category": {
                "type": "map",
                "keys": {"type": "string"},
                "values": {
                    "type": "array",
                    "items": {"type": "string"}
                }
            },
            "people_by_id": {
                "type": "map",
                "keys": {"type": "string"},
                "values": {"$ref": "#/Person"}
            },
            "team_members": {
                "type": "array",
                "items": {"$ref": "#/Person"}
            },
            "address": {"$ref": "#/Address"},
            "secondary_address": {"$ref": "#/Address", "optional": True}
        }
    },
    "Person": {
        "properties": {
            "id": {"type": "string"},
            "full_name": {"type": "string"},
            "contact": {"$ref": "#/ContactInfo"},
            "skills": {"type": "array", "items": {"type": "string"}},
            "metadata": {
                "type": "map",
                "keys": {"type": "string"},
                "values": {"type": "string"},
                "optional": True
            }
        }
    },
    "ContactInfo": {
        "properties": {
            "email": {"type": "string"},
            "phone": {"type": "string", "optional": True}
        }
    },
    "Address": {
        "properties": {
            "street": {"type": "string"},
            "city": {"type": "string"},
            "postal_code": {"type": "string"},
            "country": {"type": "string"},
            "coordinates": {
                "type": "array",
                "items": {"type": "number"}
            }
        }
    }
}

VALID_DATA_JSON = {
    "test_data": {
        "name": "John Doe",
        "age": 30,
        "salary": 75000.50,
        "is_active": True,
        "nickname": "Johnny",
        "tags": ["developer", "python", "yaml"],
        "scores": [85, 92, 78],
        "matrix": [
            [1.0, 2.0, 3.0],
            [4.0, 5.0, 6.0]
        ],
        "config": {
            "theme": "dark",
            "language": "en"
        },
        "scores_by_year": {
            "2022": 88.5,
            "2023": 92.0
        },
        "lists_by_category": {
            "programming": ["python", "javascript"],
            "databases": ["postgresql", "mongodb"]
        },
        "people_by_id": {
            "emp001": {
                "id": "emp001",
                "full_name": "Alice Smith",
                "contact": {
                    "email": "alice@example.com",
                    "phone": "+1-555-0101"
                },
                "skills": ["python", "docker"]
            },
            "emp002": {
                "id": "emp002",
                "full_name": "Bob Johnson",
                "contact": {
                    "email": "bob@example.com"
                },
                "skills": ["javascript", "react"]
            }
        },
        "team_members": [
            {
                "id": "tm001",
                "full_name": "Charlie Brown",
                "contact": {
                    "email": "charlie@example.com"
                },
                "skills": ["go", "kubernetes"]
            },
            {
                "id": "tm002",
                "full_name": "Diana Prince",
                "contact": {
                    "email": "diana@example.com",
                    "phone": "+1-555-0202"
                },
                "skills": ["rust", "webassembly"],
                "metadata": {
                    "department": "engineering",
                    "level": "senior"
                }
            }
        ],
        "address": {
            "street": "123 Main St",
            "city": "Anytown",
            "postal_code": "12345",
            "country": "USA",
            "coordinates": [40.7128, -74.0060]
        }
    }
}


class TestSchemaValidation:
    """Test all supported types in the Yaml Schema Definition Syntax"""

    def test_yaml_schema_yaml_data(self):
        """Test YAML schema with YAML data"""
        schema = load_yaml_or_json(COMPREHENSIVE_SCHEMA_YAML)
        data = load_yaml_or_json(VALID_DATA_YAML)
        assert validate_data(data, schema, raise_error=False) is True

    def test_json_schema_json_data(self):
        """Test JSON schema with JSON data"""
        assert validate_data(VALID_DATA_JSON, COMPREHENSIVE_SCHEMA_JSON, raise_error=False) is True

    def test_yaml_schema_json_data(self):
        """Test YAML schema with JSON data"""
        schema = load_yaml_or_json(COMPREHENSIVE_SCHEMA_YAML)
        assert validate_data(VALID_DATA_JSON, schema, raise_error=False) is True

    def test_json_schema_yaml_data(self):
        """Test JSON schema with YAML data"""
        data = load_yaml_or_json(VALID_DATA_YAML)
        assert validate_data(data, COMPREHENSIVE_SCHEMA_JSON, raise_error=False) is True

    def test_primitive_types(self):
        """Test all primitive types"""
        schema = {
            "<<root>>": {
                "string_field": {"type": "string"},
                "integer_field": {"type": "integer"},
                "number_field": {"type": "number"},
                "boolean_field": {"type": "boolean"}
            }
        }
        
        valid_data = {
            "string_field": "hello",
            "integer_field": 42,
            "number_field": 3.14,
            "boolean_field": True
        }
        
        assert validate_data(valid_data, schema, raise_error=False) is True

    def test_nested_arrays(self):
        """Test nested arrays (array of arrays)"""
        schema = {
            "<<root>>": {
                "matrix": {
                    "type": "array",
                    "items": {
                        "type": "array", 
                        "items": {"type": "integer"}
                    }
                }
            }
        }
        
        valid_data = {
            "matrix": [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
        }
        
        assert validate_data(valid_data, schema, raise_error=False) is True

    def test_map_types(self):
        """Test map/dictionary types"""
        schema = {
            "<<root>>": {
                "string_map": {
                    "type": "map",
                    "keys": {"type": "string"},
                    "values": {"type": "string"}
                },
                "integer_map": {
                    "type": "map", 
                    "keys": {"type": "integer"},
                    "values": {"type": "number"}
                }
            }
        }
        
        valid_data = {
            "string_map": {"key1": "value1", "key2": "value2"},
            "integer_map": {"2022": 88.5, "2023": 92.0}  # Use string keys for JSON compatibility
        }
        
        assert validate_data(valid_data, schema, raise_error=False) is True

    def test_optional_fields(self):
        """Test optional field behavior"""
        schema = {
            "<<root>>": {
                "required_field": {"type": "string"},
                "optional_field": {"type": "string", "optional": True}
            }
        }
        
        # With optional field
        data_with_optional = {
            "required_field": "present",
            "optional_field": "also present"
        }
        assert validate_data(data_with_optional, schema, raise_error=False) is True
        
        # Without optional field
        data_without_optional = {
            "required_field": "present"
        }
        assert validate_data(data_without_optional, schema, raise_error=False) is True

    def test_invalid_missing_required(self):
        """Test validation fails when required field is missing"""
        schema = {
            "<<root>>": {
                "required_field": {"type": "string"}
            }
        }
        
        invalid_data = {}  # Missing required field
        
        result = validate_data(invalid_data, schema, raise_error=False)
        assert result is not True
        assert "required_field" in result

    def test_invalid_wrong_type(self):
        """Test validation fails with wrong type"""
        schema = {
            "<<root>>": {
                "string_field": {"type": "string"}
            }
        }
        
        invalid_data = {
            "string_field": 123  # Should be string, not integer
        }
        
        result = validate_data(invalid_data, schema, raise_error=False)
        assert result is not True
        assert "is not of type 'string'" in result

    def test_invalid_additional_properties(self):
        """Test validation fails with additional properties"""
        schema = {
            "<<root>>": {
                "known_field": {"type": "string"}
            }
        }
        
        invalid_data = {
            "known_field": "value",
            "unknown_field": "should not be allowed"
        }
        
        result = validate_data(invalid_data, schema, raise_error=False)
        assert result is not True
        assert "Additional properties are not allowed" in result

    def test_invalid_map_wrong_key_type(self):
        """Test map validation fails with wrong key type"""
        schema = {
            "<<root>>": {
                "integer_keyed_map": {
                    "type": "map",
                    "keys": {"type": "integer"},
                    "values": {"type": "string"}
                }
            }
        }
        
        # This should fail because we're using string keys instead of integers
        invalid_data = {
            "integer_keyed_map": {"string_key": "value"}  # Key should be integer
        }
        
        result = validate_data(invalid_data, schema, raise_error=False)
        assert result is not True

    def test_file_based_validation(self):
        """Test validation using actual files"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Write schema file
            schema_file = os.path.join(temp_dir, "test_schema.yaml")
            with open(schema_file, 'w') as f:
                f.write(COMPREHENSIVE_SCHEMA_YAML)
            
            # Write data file
            data_file = os.path.join(temp_dir, "test_data.yaml")
            with open(data_file, 'w') as f:
                f.write(VALID_DATA_YAML)
            
            # Load and validate
            schema = load_file(schema_file)
            data = load_file(data_file)
            
            assert validate_data(data, schema, raise_error=False) is True


if __name__ == "__main__":
    pytest.main([__file__])

