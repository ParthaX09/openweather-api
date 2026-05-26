import json
from pathlib import Path
from typing import Any, Union, Dict
import jsonschema
from jsonschema import validate, Draft7Validator
from utils.logger import logger

# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent
SCHEMAS_DIR = BASE_DIR / "schemas"

class SchemaValidator:
    """Helper class to load JSON schemas and validate API responses against them."""

    @staticmethod
    def load_schema(schema_name: str) -> Dict[str, Any]:
        """Loads a JSON schema file from the schemas/ directory."""
        schema_path = SCHEMAS_DIR / schema_name
        if not schema_path.exists():
            raise FileNotFoundError(f"Schema file not found at {schema_path}")
        
        with open(schema_path, "r", encoding="utf-8") as f:
            return json.load(f)

    @classmethod
    def validate_json(cls, data: Union[Dict[str, Any], list], schema_name: str) -> bool:
        """
        Validates json data against a schema.
        
        Args:
            data: The parsed JSON object or list.
            schema_name: File name of the schema in schemas/ (e.g. 'weather_schema.json').
            
        Raises:
            jsonschema.exceptions.ValidationError: If data does not match the schema.
        """
        schema = cls.load_schema(schema_name)
        validator = Draft7Validator(schema)
        
        errors = sorted(validator.iter_errors(data), key=lambda e: e.path)
        if errors:
            error_details = []
            for err in errors:
                path = " -> ".join([str(p) for p in err.path]) or "root"
                error_details.append(f"[{path}]: {err.message}")
            
            error_msg = f"Schema validation failed for {schema_name}:\n" + "\n".join(error_details)
            logger.error(error_msg)
            raise jsonschema.exceptions.ValidationError(error_msg)

        logger.info(f"Schema validation passed successfully for {schema_name}.")
        return True
    
    @classmethod
    def is_valid(cls, data: Union[Dict[str, Any], list], schema_name: str) -> bool:
        """Returns True if valid, False otherwise, without raising an exception."""
        try:
            cls.validate_json(data, schema_name)
            return True
        except jsonschema.exceptions.ValidationError:
            return False
        except Exception as e:
            logger.error(f"Unexpected error validating schema: {e}")
            return False
