import json
import yaml
import os
from typing import Dict, Any, Optional
import logging

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
        """Load and cache the model manifest.
        
        Returns:
            Dict: The model manifest
        
        Raises:
            FileNotFoundError: If manifest does not exist
        """
        if self._manifest is not None:
            return self._manifest
            
        manifest_path = os.path.join(self.artifacts_dir, 'selected_models_v1.json')
        if not os.path.exists(manifest_path):
            raise FileNotFoundError(f"Model manifest not found at {manifest_path}")
            
        with open(manifest_path, 'r') as f:
            self._manifest = json.load(f)
            
        return self._manifest

    def load_preprocessor_config(self) -> Dict[str, Any]:
        """Load and cache the preprocessor configuration."""
        if self._preprocessor_config is not None:
            return self._preprocessor_config
            
        config_path = os.path.join(self.artifacts_dir, 'mock_preprocessor_v1.json')
        if not os.path.exists(config_path):
            self._preprocessor_config = {}
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
            self._feature_schema = {}
        else:
            with open(schema_path, 'r') as f:
                self._feature_schema = yaml.safe_load(f)
                
        return self._feature_schema

    def get_task_config(self, task_name: str) -> Dict[str, Any]:
        """Get configuration for a specific task from manifest.
        
        Args:
            task_name: Name of the task
            
        Returns:
            Dict: Configuration for the task
            
        Raises:
            KeyError: If task not found in manifest
        """
        manifest = self.load_model_manifest()
        if 'tasks' not in manifest or task_name not in manifest['tasks']:
            raise KeyError(f"Task {task_name} not found in manifest")
        return manifest['tasks'][task_name]

    def get_model_hash(self) -> str:
        """Get a composite model hash from per-task hashes in the manifest.

        Returns:
            str: Composite hash string built from all task model_hash values.
        """
        import hashlib
        manifest = self.load_model_manifest()
        tasks = manifest.get('tasks', {})
        parts = sorted(
            f"{name}:{cfg.get('model_hash', 'none')}"
            for name, cfg in tasks.items()
        )
        composite = "|".join(parts)
        return hashlib.md5(composite.encode()).hexdigest()[:16]
