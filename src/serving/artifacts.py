import json
import yaml
import os
from typing import Dict, Any, Optional
import logging
from src.serving.validation import ArtifactLoadError, ArtifactMismatchError

class ArtifactLoader:
    """Loads artifacts for prediction serving."""
    
    def __init__(self, artifacts_dir: Optional[str] = None):
        """Initialize loader with artifact directory.
        
        Args:
            artifacts_dir: Path to directory containing artifacts
        """
        self.artifacts_dir = artifacts_dir or os.path.join(os.getcwd(), 'artifacts', 'mock')
        self._manifest: Optional[Dict] = None
        self._preprocessor_config: Optional[Dict] = None
        self._feature_schema: Optional[Dict] = None

    def load_model_manifest(self) -> Dict[str, Any]:
        """Load and cache the model manifest."""
        if self._manifest is not None:
            return self._manifest
            
        manifest_path = os.path.join(self.artifacts_dir, 'selected_models_v1.json')
        if not os.path.exists(manifest_path):
            raise FileNotFoundError(f"Model manifest not found at {manifest_path}")
            
        with open(manifest_path, 'r') as f:
            self._manifest = json.load(f)
            
        self.validate_artifacts(self._manifest)
            
        return self._manifest

    def load_preprocessor_config(self) -> Dict[str, Any]:
        """Load and cache the preprocessor configuration."""
        if self._preprocessor_config is not None:
            return self._preprocessor_config
            
        config_path = os.path.join(self.artifacts_dir, 'mock_preprocessor_v1.json')
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Preprocessor config not found at {config_path}")
        else:
            with open(config_path, 'r') as f:
                self._preprocessor_config = json.load(f)
                
        return self._preprocessor_config

    def load_feature_schema(self) -> Dict[str, Any]:
        """Load and cache the feature schema."""
        if self._feature_schema is not None:
            return self._feature_schema
            
        schema_path = os.path.join(self.artifacts_dir, 'feature_schema_v1.yaml')
        if not os.path.exists(schema_path):
            raise FileNotFoundError(f"Feature schema not found at {schema_path}")
        else:
            with open(schema_path, 'r') as f:
                self._feature_schema = yaml.safe_load(f)
                
        return self._feature_schema

    def validate_artifacts(self, manifest: Dict[str, Any]) -> None:
        """Validate artifact compatibility."""
        preprocessor = self.load_preprocessor_config()
        feature_schema = self.load_feature_schema()
        
        # Check global version from schema
        if feature_schema.get('version') != 'feature_schema_v1':
            raise ArtifactMismatchError("Feature schema version mismatch.")
        
        # Check preprocessor version compatibility per task
        preproc_version = preprocessor.get('version', 'mock_preprocessor_v1')
        for task_name, config in manifest.get('tasks', {}).items():
            if config.get('preprocessor_version') != preproc_version:
                raise ArtifactMismatchError(
                    f"Preprocessor version mismatch for task {task_name}. "
                    f"Expected {config.get('preprocessor_version')} but got {preproc_version}"
                )
            # Ensure model family matches explanation method conceptually
            family = config.get('family', '').lower()
            if family not in ['xgboost', 'gru', 'mock']:
                raise ArtifactMismatchError(f"Unsupported model family {family}")

    def get_task_config(self, task_name: str) -> Dict[str, Any]:
        """Get configuration for a specific task from manifest."""
        manifest = self.load_model_manifest()
        if 'tasks' not in manifest or task_name not in manifest['tasks']:
            raise KeyError(f"Task {task_name} not found in manifest")
        return manifest['tasks'][task_name]

    def get_model_hash(self) -> str:
        """Get a composite model hash from per-task hashes in the manifest."""
        import hashlib
        manifest = self.load_model_manifest()
        tasks = manifest.get('tasks', {})
        parts = sorted(
            f"{name}:{cfg.get('model_hash', 'none')}"
            for name, cfg in tasks.items()
        )
        composite = "|".join(parts)
        return hashlib.md5(composite.encode()).hexdigest()[:16]
