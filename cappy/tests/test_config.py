"""Unit tests for cappy.config module."""

import pytest
import tempfile
from pathlib import Path
from cappy.config import (
    CappyConfig,
    validate_config,
    get_typed_config,
    load_config,
)


class TestCappyConfig:
    """Tests for CappyConfig dataclass."""
    
    @pytest.mark.unit
    def test_default_config(self):
        """Test default configuration values."""
        config = CappyConfig()
        
        assert config.default_model == "o1"
        assert len(config.allowed_models) > 0
        assert config.max_files_touched_per_run == 5
        assert config.max_iterations == 20
        assert config.require_plan is True
        assert config.block_dangerous_commands is True
    
    @pytest.mark.unit
    def test_config_validation_valid(self):
        """Test validation of valid config."""
        config = CappyConfig()
        errors = config.validate()
        
        assert len(errors) == 0
    
    @pytest.mark.unit
    def test_config_validation_invalid_max_files(self):
        """Test validation catches invalid max_files."""
        config = CappyConfig(max_files_touched_per_run=0)
        errors = config.validate()
        
        assert len(errors) > 0
        assert any("max_files_touched_per_run" in e for e in errors)
    
    @pytest.mark.unit
    def test_config_validation_invalid_timeout(self):
        """Test validation catches invalid timeout."""
        config = CappyConfig(api_timeout=5)
        errors = config.validate()
        
        assert len(errors) > 0
        assert any("api_timeout" in e for e in errors)
    
    @pytest.mark.unit
    def test_config_validation_empty_models(self):
        """Test validation catches empty allowed_models."""
        config = CappyConfig(allowed_models=[])
        errors = config.validate()
        
        assert len(errors) > 0
        assert any("allowed_models" in e for e in errors)


class TestConfigValidation:
    """Tests for config validation function."""
    
    @pytest.mark.unit
    def test_validate_default_config(self):
        """Test validating default config."""
        is_valid, errors = validate_config()
        
        # Default config should be valid
        assert is_valid or len(errors) == 0
    
    @pytest.mark.unit
    def test_validate_yaml_file(self):
        """Test validating YAML config file."""
        # Create temporary config file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
default_model: gpt-4.1
max_files_touched_per_run: 10
require_plan: true
""")
            config_path = f.name
        
        try:
            is_valid, errors = validate_config(config_path)
            assert is_valid or len(errors) == 0
        finally:
            Path(config_path).unlink(missing_ok=True)
    
    @pytest.mark.unit
    def test_validate_invalid_yaml(self):
        """Test validating invalid YAML."""
        # Create temporary invalid config file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
max_files_touched_per_run: -1
api_timeout: 5
""")
            config_path = f.name
        
        try:
            is_valid, errors = validate_config(config_path)
            assert not is_valid
            assert len(errors) > 0
        finally:
            Path(config_path).unlink(missing_ok=True)


class TestConfigLoading:
    """Tests for config loading."""
    
    @pytest.mark.unit
    def test_load_default_config(self):
        """Test loading default config."""
        config = load_config()
        
        assert isinstance(config, dict)
        assert "allowed_models" in config or "default_model" in config
    
    @pytest.mark.unit
    def test_get_typed_config(self):
        """Test getting typed config object."""
        config = get_typed_config()
        
        assert isinstance(config, CappyConfig)
        assert hasattr(config, "default_model")
        assert hasattr(config, "max_iterations")
