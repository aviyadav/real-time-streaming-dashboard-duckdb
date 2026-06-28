#!/usr/bin/env python3
"""
Post-install patch for mashumaro + dbt-duckdb compatibility.

The mashumaro library's JSONObjectSchema class (in jsonschema/models.py)
crashes at class-definition time because mashumaro's own metaclass
(DataClassDictMixin.__init_subclass__) cannot build an unpacker for
the inherited `schema: Optional[str]` field when JSONObjectSchema
overrides the `type` field with a narrower (non-Optional) annotation.

This manifests as:
  mashumaro.exceptions.UnserializableField:
      Field "schema" of type Optional[str] in JSONObjectSchema is not serializable

The fix: add an explicit Config to JSONObjectSchema that inherits from
JSONSchema.Config, ensuring consistent metaclass behavior.
"""
import sys
from pathlib import Path


def find_mashumaro_models() -> Path:
    """Locate the installed mashumaro/jsonschema/models.py."""
    for p in sys.path:
        candidate = Path(p) / "mashumaro" / "jsonschema" / "models.py"
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(
        "Could not find mashumaro/jsonschema/models.py in sys.path"
    )


def patch_models_file(path: Path) -> bool:
    """Apply the fix to JSONObjectSchema and JSONArraySchema."""
    content = path.read_text(encoding="utf-8")

    # The fix: add a Config inner class to JSONObjectSchema that inherits
    # from JSONSchema.Config, and similarly for JSONArraySchema.
    # This ensures the metaclass uses the same serialization settings.

    # Patch 1: JSONObjectSchema
    old_obj = "@dataclass\nclass JSONObjectSchema(JSONSchema):"
    new_obj = """@dataclass
class JSONObjectSchema(JSONSchema):
    class Config(JSONSchema.Config):
        pass"""

    if new_obj in content:
        print("  JSONObjectSchema already patched — skipping")
    elif old_obj in content:
        content = content.replace(old_obj, new_obj)
        print("  ✓ Patched JSONObjectSchema")
    else:
        print("  ⚠ Could not find JSONObjectSchema pattern — may already be fixed")
        # Try alternate patterns for different mashumaro versions
        alt_old = "@dataclass\nclass JSONObjectSchema(JSONSchema):\n    type:"
        if alt_old in content:
            # Insert Config before the type override
            indent = "    "
            alt_new = (
                "@dataclass\n"
                "class JSONObjectSchema(JSONSchema):\n"
                f"{indent}class Config(JSONSchema.Config):\n"
                f"{indent}    pass\n"
                f"{indent}\n"
                f"{indent}type:"
            )
            content = content.replace(alt_old, alt_new)
            print("  ✓ Patched JSONObjectSchema (alternate pattern)")

    # Patch 2: JSONArraySchema (same pattern, for safety)
    old_arr = "@dataclass\nclass JSONArraySchema(JSONSchema):"
    new_arr = """@dataclass
class JSONArraySchema(JSONSchema):
    class Config(JSONSchema.Config):
        pass"""

    if new_arr in content:
        print("  JSONArraySchema already patched — skipping")
    elif old_arr in content:
        content = content.replace(old_arr, new_arr)
        print("  ✓ Patched JSONArraySchema")
    else:
        alt_old_arr = "@dataclass\nclass JSONArraySchema(JSONSchema):\n    type:"
        if alt_old_arr in content:
            indent = "    "
            alt_new_arr = (
                "@dataclass\n"
                "class JSONArraySchema(JSONSchema):\n"
                f"{indent}class Config(JSONSchema.Config):\n"
                f"{indent}    pass\n"
                f"{indent}\n"
                f"{indent}type:"
            )
            content = content.replace(alt_old_arr, alt_new_arr)
            print("  ✓ Patched JSONArraySchema (alternate pattern)")

    path.write_text(content, encoding="utf-8")
    return True


def main():
    print("=== mashumaro dbt-duckdb compatibility patch ===")
    try:
        models_path = find_mashumaro_models()
        print(f"Found: {models_path}")
        patch_models_file(models_path)
        print("✓ Patch applied successfully")
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        print("Is mashumaro installed? Run: pip install mashumaro")
        sys.exit(1)


if __name__ == "__main__":
    main()
