# Utility script to generate a sample ProjectConfig YAML.
# Not used in runtime – useful for onboarding and CI.

from shared_tools.project_config import ProjectConfig
import yaml

if __name__ == "__main__":
    default = ProjectConfig.create_default_config_object()
    yaml.safe_dump(default, open("config.schema.yaml", "w"), sort_keys=False)

# Example usage:
# python tools/gen_config_schema.py
