#!/usr/bin/env python3
"""
Validate aspect builders in dataproduct.py against deployed GCP Dataplex AspectTypes.

This script helps catch drift between:
- AspectTypes deployed in GCP (dataproducts-aspect-types/Pulumi.yaml)
- Aspect builders in the component (dataproduct.py)
- schema.json input properties

Usage:
    python validate_aspects.py [--project PROJECT] [--location LOCATION]
"""

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional


def run_gcloud_command(cmd: List[str]) -> Optional[str]:
    """Run a gcloud command and return the output."""
    try:
        # On Windows, we need to use gcloud.cmd instead of gcloud
        if os.name == 'nt' and cmd[0] == 'gcloud':
            cmd[0] = 'gcloud.cmd'
        result = subprocess.run(cmd, capture_output=True, text=True, check=True, shell=False)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"[!] Error running gcloud command: {e.stderr}", file=sys.stderr)
        return None


def get_deployed_aspect_types(project: str, location: str) -> Dict[str, Dict]:
    """Query GCP for deployed aspect types."""
    print(f"[*] Querying deployed aspect types in {project}/{location}...")

    cmd = [
        "gcloud", "dataplex", "aspect-types", "list",
        f"--project={project}",
        f"--location={location}",
        "--format=json"
    ]

    output = run_gcloud_command(cmd)
    if not output:
        return {}

    aspect_types = json.loads(output)

    # Index by aspect type ID
    result = {}
    for aspect_type in aspect_types:
        aspect_id = aspect_type.get("name", "").split("/")[-1]
        if aspect_id:
            result[aspect_id] = aspect_type

    print(f"   Found {len(result)} deployed aspect types\n")
    return result


def extract_aspect_fields(metadata_template) -> Set[str]:
    """Extract field names from aspect metadata template."""
    try:
        # Handle both dict and string formats
        if isinstance(metadata_template, str):
            template = json.loads(metadata_template)
        elif isinstance(metadata_template, dict):
            template = metadata_template
        else:
            return set()
    except json.JSONDecodeError:
        return set()

    fields = set()
    if "recordFields" in template:
        for record_field in template["recordFields"]:
            if record_field.get("type") == "record" and "recordFields" in record_field:
                for field in record_field["recordFields"]:
                    field_name = field.get("name")
                    if field_name:
                        fields.add(field_name)

    return fields


def parse_aspect_registry_from_code() -> List[Tuple[str, str]]:
    """Parse ASPECT_REGISTRY from dataproduct.py."""
    code_path = Path(__file__).parent.parent / "dataproduct.py"

    if not code_path.exists():
        print(f"[!] Could not find dataproduct.py at {code_path}", file=sys.stderr)
        return []

    content = code_path.read_text()

    # Find ASPECT_REGISTRY definition
    registry_match = re.search(
        r'ASPECT_REGISTRY\s*=\s*\[(.*?)\]',
        content,
        re.DOTALL
    )

    if not registry_match:
        print("[!] Could not find ASPECT_REGISTRY in dataproduct.py", file=sys.stderr)
        return []

    registry_content = registry_match.group(1)

    # Extract aspect type IDs and builder methods
    aspects = []
    aspect_configs = re.findall(
        r'AspectConfig\s*\((.*?)\)',
        registry_content,
        re.DOTALL
    )

    for config in aspect_configs:
        # Extract aspect_type_id
        type_id_match = re.search(r'aspect_type_id\s*=\s*["\']([^"\']+)["\']', config)
        # Extract builder_method
        builder_match = re.search(r'builder_method\s*=\s*["\']([^"\']+)["\']', config)

        if type_id_match and builder_match:
            aspects.append((type_id_match.group(1), builder_match.group(1)))

    return aspects


def extract_builder_fields(builder_method: str, code_content: str) -> Set[str]:
    """Extract field names from a builder method in the code."""
    # Find the builder method definition
    method_pattern = rf'def {builder_method}\(self.*?\).*?:\s*""".*?"""(.*?)(?=\n    def |\n\nclass |\Z)'
    method_match = re.search(method_pattern, code_content, re.DOTALL)

    if not method_match:
        return set()

    method_body = method_match.group(1)

    # Extract field names from return statement
    # Look for patterns like "field_name": value or 'field_name': value
    fields = set()
    field_matches = re.findall(r'["\']([a-z_][a-z0-9_]*)["\']:\s*', method_body)
    fields.update(field_matches)

    return fields


def validate_aspects(project: str, location: str) -> bool:
    """Validate aspect configuration."""
    print("=" * 70)
    print("ASPECT VALIDATION REPORT")
    print("=" * 70)
    print()

    # Get deployed aspect types from GCP
    deployed_aspects = get_deployed_aspect_types(project, location)

    # Parse aspect registry from code
    print("[*] Parsing ASPECT_REGISTRY from dataproduct.py...")
    registry_aspects = parse_aspect_registry_from_code()

    if not registry_aspects:
        print("[!] No aspects found in ASPECT_REGISTRY\n")
        return False

    print(f"   Found {len(registry_aspects)} aspects in registry\n")

    # Load code for field extraction
    code_path = Path(__file__).parent.parent / "dataproduct.py"
    code_content = code_path.read_text()

    all_valid = True

    # Validate each aspect
    for aspect_id, builder_method in registry_aspects:
        print(f"[-] {aspect_id}")
        print(f"   Builder: {builder_method}")

        # Check if deployed
        if aspect_id not in deployed_aspects:
            print(f"   [!] NOT DEPLOYED in GCP")
            all_valid = False
            print()
            continue

        # Get deployed fields
        deployed_aspect = deployed_aspects[aspect_id]
        metadata_template = deployed_aspect.get("metadataTemplate", "{}")
        deployed_fields = extract_aspect_fields(metadata_template)

        # Get builder fields
        builder_fields = extract_builder_fields(builder_method, code_content)

        if not builder_fields:
            print(f"   [?]  Could not parse builder method fields")
            print()
            continue

        # Compare fields
        missing_in_builder = deployed_fields - builder_fields
        extra_in_builder = builder_fields - deployed_fields

        if missing_in_builder:
            print(f"   [?]  Missing in builder: {', '.join(sorted(missing_in_builder))}")
            all_valid = False

        if extra_in_builder:
            print(f"   [?]  Extra in builder: {', '.join(sorted(extra_in_builder))}")
            all_valid = False

        if not missing_in_builder and not extra_in_builder:
            print(f"   [+] All {len(deployed_fields)} fields match")
        else:
            print(f"   Deployed: {len(deployed_fields)} fields")
            print(f"   Builder:  {len(builder_fields)} fields")

        print()

    # Check for deployed aspects not in registry
    registry_ids = {aspect_id for aspect_id, _ in registry_aspects}
    deployed_ids = set(deployed_aspects.keys())
    unregistered = deployed_ids - registry_ids

    if unregistered:
        print("[?]  Deployed aspect types NOT in ASPECT_REGISTRY:")
        for aspect_id in sorted(unregistered):
            print(f"   - {aspect_id}")
        print()

    # Summary
    print("=" * 70)
    if all_valid and not unregistered:
        print("[+] VALIDATION PASSED - All aspects are in sync!")
    else:
        print("[!] VALIDATION FAILED - Please review issues above")
        print()
        print("Next steps:")
        print("1. Update builder methods in dataproduct.py to match deployed schemas")
        print("2. Update schema.json with any new required input properties")
        print("3. Re-run this validation script")
    print("=" * 70)

    return all_valid and not unregistered


def main():
    parser = argparse.ArgumentParser(
        description="Validate aspect configuration against GCP Dataplex"
    )
    parser.add_argument(
        "--project",
        default="cubedev2-lab-1c497b",
        help="GCP project ID (default: cubedev2-lab-1c497b)"
    )
    parser.add_argument(
        "--location",
        default="northamerica-northeast1",
        help="GCP location (default: northamerica-northeast1)"
    )

    args = parser.parse_args()

    try:
        success = validate_aspects(args.project, args.location)
        sys.exit(0 if success else 1)

    except Exception as e:
        print(f"\n[!] Unexpected error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
