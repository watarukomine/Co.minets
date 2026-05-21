import json
import sys

try:
    with open("C:/Users/00137012/.gemini/antigravity/brain/da0fa027-3e89-4897-85ce-b8af11f85d35/.system_generated/steps/486/content.md", "r", encoding="utf-8") as f:
        content = f.read()
        # Find the JSON part
        json_start = content.find("{")
        if json_start != -1:
            json_str = content[json_start:]
            data = json.loads(json_str)
            fields = data.get("fields", {})
            print("KEYS in fields:", list(fields.keys()))
            if "classes" in fields:
                print("CLASSES len:", len(fields["classes"].get("arrayValue", {}).get("values", [])))
            if "factorTypes" in fields:
                print("FACTOR TYPES len:", len(fields["factorTypes"].get("arrayValue", {}).get("values", [])))
except Exception as e:
    print("Error:", e)
