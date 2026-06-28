#!/usr/bin/env python3
"""
Fix the mashumaro + dbt compatibility crash by patching JSONObjectSchema.

Root cause:
  mashumaro's jsonschema/models.py defines:
    @dataclass
    class JSONObjectSchema(JSONSchema):
        type: JSONSchemaInstanceType = JSONSchemaInstanceType.OBJECT

  JSONObjectSchema inherits fields from JSONSchema (including
  'schema: Optional[str]') but does NOT inherit JSONSchema.Config.
  Mashumaro does not support Config inheritance — a class without its
  own Config gets BaseConfig (empty defaults). This causes the metaclass
  (DataClassDictMixin.__init_subclass__) to fail when building the
  unpacker for the inherited 'schema' field.

  Error: UnserializableField: Field "schema" of type Optional[str]
         in JSONObjectSchema is not serializable

Fix:
  Add 'class Config(JSONSchema.Config): pass' to JSONObjectSchema and
  JSONArraySchema so they inherit the parent's serialization settings.
"""
import sys
from pathlib import Path


def find_models_file() -> Path:
    for p in sys.path:
        candidate = Path(p) / "mashumaro" / "jsonschema" / "models.py"
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(
        "Could not find mashumaro/jsonschema/models.py in sys.path"
    )


def patch(path: Path) -> None:
    content = path.read_text(encoding="utf-8")
    original = content

    # ── Strategy: add Config inheritance to JSONObjectSchema ──────
    # Match both old-style (Optional) and new-style (str | None) annotations
    import re

    # Pattern for JSONObjectSchema — matches across mashumaro versions
    # We look for the class definition and insert Config right after it
    obj_pattern = r'(@dataclass\nclass JSONObjectSchema\(JSONSchema\):\n    )'
    if re.search(obj_pattern, content):
        content = re.sub(
            obj_pattern,
            r'\1class Config(JSONSchema.Config):\n        pass\n\n    ',
            content,
        )
        print("  [OK] Added Config to JSONObjectSchema")

    # Pattern for JSONArraySchema (same issue, for safety)
    arr_pattern = r'(@dataclass\nclass JSONArraySchema\(JSONSchema\):\n    )'
    if re.search(arr_pattern, content):
        content = re.sub(
            arr_pattern,
            r'\1class Config(JSONSchema.Config):\n        pass\n\n    ',
            content,
        )
        print("  [OK] Added Config to JSONArraySchema")

    if content == original:
        print("  [WARN] No patterns matched -- file may already be patched or")
        print("    have a different structure. Trying alternative patterns...")
        # Try alternative: JSONObjectSchema on a single line
        alt = re.search(
            r"class JSONObjectSchema\(JSONSchema\):\n( +)type:",
            content,
        )
        if alt:
            indent = alt.group(1)
            content = content.replace(
                f"class JSONObjectSchema(JSONSchema):\n{indent}type:",
                f"class JSONObjectSchema(JSONSchema):\n"
                f"{indent}class Config(JSONSchema.Config):\n"
                f"{indent}    pass\n{indent}\n"
                f"{indent}type:",
            )
            print("  [OK] Patched JSONObjectSchema (alt pattern)")

        alt2 = re.search(
            r"class JSONArraySchema\(JSONSchema\):\n( +)type:",
            content,
        )
        if alt2:
            indent2 = alt2.group(1)
            content = content.replace(
                f"class JSONArraySchema(JSONSchema):\n{indent2}type:",
                f"class JSONArraySchema(JSONSchema):\n"
                f"{indent2}class Config(JSONSchema.Config):\n"
                f"{indent2}    pass\n{indent2}\n"
                f"{indent2}type:",
            )
            print("  [OK] Patched JSONArraySchema (alt pattern)")

    path.write_text(content, encoding="utf-8")
    if content != original:
        print("  [OK] File updated")


def main():
    print("=== mashumaro JSONObjectSchema fix ===")
    try:
        filepath = find_models_file()
        print(f"Found: {filepath}")
        patch(filepath)
        print("[OK] Patch applied -- dbt should now work")
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
