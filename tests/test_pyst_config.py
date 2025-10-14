"""Tests for PyST API configuration."""

import os
import pytest
from pathlib import Path
from unittest.mock import Mock, patch
import importlib.util


def load_config_module():
    """Load config module directly without importing the package."""
    # Get the path relative to the test file
    test_dir = Path(__file__).parent
    repo_root = test_dir.parent
    config_path = repo_root / 'trailpack' / 'pyst' / 'api' / 'config.py'
    
    spec = importlib.util.spec_from_file_location(
        'config',
        str(config_path)
    )
    config_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(config_module)
    return config_module


def test_config_loads_from_environment_variables():
    """Test that config loads from environment variables."""
    with patch.dict(os.environ, {
        'PYST_HOST': 'http://test-host:8000',
        'PYST_AUTH_TOKEN': 'test-token',
        'PYST_TIMEOUT': '60'
    }):
        config_module = load_config_module()
        config = config_module.config
        
        assert config.host == 'http://test-host:8000'
        assert config.auth_token == 'test-token'
        assert config.timeout == 60


def test_config_uses_defaults_when_no_env():
    """Test that config uses default values when no environment variables are set."""
    with patch.dict(os.environ, {}, clear=True):
        config_module = load_config_module()
        config = config_module.config
        
        assert config.host == 'http://localhost:8000'
        assert config.auth_token is None
        assert config.timeout == 30


def test_config_loads_from_streamlit_secrets():
    """Test that config loads from Streamlit secrets."""
    # Clear environment variables
    with patch.dict(os.environ, {}, clear=True):
        # Mock streamlit with secrets
        mock_st = Mock()
        mock_st.secrets = {
            'PYST_HOST': 'http://streamlit-host:9000',
            'PYST_AUTH_TOKEN': 'streamlit-token'
        }
        
        with patch.dict('sys.modules', {'streamlit': mock_st}):
            config_module = load_config_module()
            config = config_module.config
            
            assert config.host == 'http://streamlit-host:9000'
            assert config.auth_token == 'streamlit-token'


def test_config_prioritizes_streamlit_secrets_over_env():
    """Test that Streamlit secrets take priority over environment variables."""
    with patch.dict(os.environ, {
        'PYST_HOST': 'http://env-host:7000',
        'PYST_AUTH_TOKEN': 'env-token'
    }):
        # Mock streamlit with secrets
        mock_st = Mock()
        mock_st.secrets = {
            'PYST_HOST': 'http://streamlit-host:9000',
            'PYST_AUTH_TOKEN': 'streamlit-token'
        }
        
        with patch.dict('sys.modules', {'streamlit': mock_st}):
            config_module = load_config_module()
            config = config_module.config
            
            # Streamlit secrets should win
            assert config.host == 'http://streamlit-host:9000'
            assert config.auth_token == 'streamlit-token'


def test_config_handles_missing_streamlit_secrets_gracefully():
    """Test that config falls back to env when Streamlit secrets are missing."""
    with patch.dict(os.environ, {
        'PYST_HOST': 'http://env-host:7000',
        'PYST_AUTH_TOKEN': 'env-token'
    }):
        # Mock streamlit with partial secrets
        mock_st = Mock()
        mock_st.secrets = {}
        
        with patch.dict('sys.modules', {'streamlit': mock_st}):
            config_module = load_config_module()
            config = config_module.config
            
            # Should fall back to environment variables
            assert config.host == 'http://env-host:7000'
            assert config.auth_token == 'env-token'


def test_config_lazy_loading():
    """Test that config uses lazy loading via proxy."""
    with patch.dict(os.environ, {
        'PYST_HOST': 'http://test-host:8000',
        'PYST_AUTH_TOKEN': 'test-token'
    }):
        config_module = load_config_module()
        
        # Access config - this should trigger lazy loading
        config = config_module.config
        assert hasattr(config, 'host')
        assert config.host == 'http://test-host:8000'
        
        # Call get_config() directly
        direct_config = config_module.get_config()
        assert direct_config.host == 'http://test-host:8000'
        assert direct_config.auth_token == 'test-token'


def test_config_handles_streamlit_import_error():
    """Test that config works when streamlit is not available."""
    with patch.dict(os.environ, {
        'PYST_HOST': 'http://env-host:7000',
        'PYST_AUTH_TOKEN': 'env-token'
    }):
        # Mock streamlit as None (not available)
        with patch.dict('sys.modules', {'streamlit': None}):
            config_module = load_config_module()
            config = config_module.config
            
            assert config.host == 'http://env-host:7000'
            assert config.auth_token == 'env-token'


def test_config_handles_streamlit_secrets_exception():
    """Test that config handles exceptions when accessing Streamlit secrets."""
    with patch.dict(os.environ, {
        'PYST_HOST': 'http://env-host:7000',
        'PYST_AUTH_TOKEN': 'env-token'
    }):
        # Mock streamlit that raises exception on secrets access
        mock_st = Mock()
        mock_st.secrets = Mock(side_effect=Exception("Secrets not available"))
        
        with patch.dict('sys.modules', {'streamlit': mock_st}):
            config_module = load_config_module()
            config = config_module.config
            
            # Should fall back to environment variables
            assert config.host == 'http://env-host:7000'
            assert config.auth_token == 'env-token'
