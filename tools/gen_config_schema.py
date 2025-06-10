"""
Module: gen_config_schema
Purpose: Generate a default ProjectConfig YAML schema.
"""

from shared_tools.project_config import ProjectConfig
import yaml

if __name__ == "__main__":
    default = ProjectConfig.create_default_config_object()
    yaml.safe_dump(default, open("config.schema.yaml", "w"), sort_keys=False)

# Example usage:
# python tools/gen_config_schema.py
