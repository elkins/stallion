"""
Basic unit tests for Stallion package manager.

Run with: pytest tests/
"""
import pytest
from stallion import metadata
from stallion.compat import (
    get_distribution, working_set, parse_version, 
    iter_entry_points, DistributionWrapper
)


class TestMetadataParsing:
    """Tests for metadata parsing functionality."""
    
    def test_parse_metadata_basic(self):
        """Test basic metadata parsing with version 1.0."""
        test_metadata = """Metadata-Version: 1.0
Name: test-package
Version: 1.0.0
Summary: A test package
"""
        parsed, known_keys = metadata.parse_metadata(test_metadata)
        
        assert parsed['Name'] == 'test-package'
        assert parsed['Version'] == '1.0.0'
        assert 'name' in known_keys
        assert 'version' in known_keys
    
    def test_parse_metadata_no_version(self):
        """Test metadata parsing without explicit version (defaults to 1.0)."""
        test_metadata = """Name: test-package
Version: 1.0.0
"""
        parsed, known_keys = metadata.parse_metadata(test_metadata)
        
        # Should default to version 1.0
        assert parsed['Name'] == 'test-package'
        assert len(known_keys) > 0
    
    def test_metadata_to_dict(self):
        """Test converting parsed metadata to dictionary."""
        test_metadata = """Metadata-Version: 1.0
Name: test-package
Version: 1.0.0
Summary: A test package
Author: Test Author
"""
        parsed, known_keys = metadata.parse_metadata(test_metadata)
        result = metadata.metadata_to_dict(parsed, known_keys)
        
        assert 'name' in result
        assert 'version' in result
        assert result['name'] == 'test-package'
        assert result['version'] == '1.0.0'
    
    def test_field_process_unknown(self):
        """Test field processing converts UNKNOWN to None."""
        result = metadata.field_process('summary', 'UNKNOWN')
        assert result is None
    
    def test_field_process_list(self):
        """Test field processing handles lists."""
        test_list = ['item1', 'item2']
        result = metadata.field_process('requires', test_list)
        assert result == test_list
    
    def test_field_process_classifier(self):
        """Test classifier field processing into nested dict."""
        classifiers = [
            'Development Status :: 4 - Beta',
            'License :: OSI Approved :: Apache Software License'
        ]
        result = metadata.field_process('classifier', classifiers)
        
        assert isinstance(result, dict)
        assert 'Development Status' in result
        assert 'License' in result


class TestCompatibilityLayer:
    """Tests for pkg_resources compatibility layer."""
    
    def test_working_set_iteration(self):
        """Test iterating over working set."""
        dists = list(working_set)
        
        assert len(dists) > 0
        assert all(isinstance(d, DistributionWrapper) for d in dists)
    
    def test_working_set_length(self):
        """Test working set has length."""
        length = len(working_set)
        assert length > 0
        assert isinstance(length, int)
    
    def test_get_distribution(self):
        """Test getting a specific distribution."""
        # setuptools should always be available
        dist = get_distribution('setuptools')
        
        assert dist.project_name.lower() == 'setuptools'
        assert hasattr(dist, 'version')
        assert dist.version is not None
    
    def test_distribution_attributes(self):
        """Test distribution wrapper has expected attributes."""
        dist = get_distribution('setuptools')
        
        assert hasattr(dist, 'project_name')
        assert hasattr(dist, 'version')
        assert hasattr(dist, 'location')
        assert hasattr(dist, 'key')
        assert dist.key == dist.project_name.lower()
    
    def test_distribution_get_entry_map(self):
        """Test getting entry points map."""
        dist = get_distribution('setuptools')
        entry_map = dist.get_entry_map()
        
        assert isinstance(entry_map, dict)
        # setuptools has console_scripts
        if 'console_scripts' in entry_map:
            assert isinstance(entry_map['console_scripts'], dict)
    
    def test_parse_version(self):
        """Test version parsing and comparison."""
        v1 = parse_version('1.0.0')
        v2 = parse_version('2.0.0')
        v3 = parse_version('1.0.0')
        
        assert v2 > v1
        assert v1 < v2
        assert v1 == v3
    
    def test_iter_entry_points_console_scripts(self):
        """Test iterating console script entry points."""
        scripts = list(iter_entry_points('console_scripts'))
        
        # Should have at least some console scripts
        assert len(scripts) > 0
        
        # Check structure
        for ep in scripts[:5]:  # Check first 5
            assert hasattr(ep, 'name')
            assert isinstance(ep.name, str)
    
    def test_distribution_requires(self):
        """Test getting distribution requirements."""
        dist = get_distribution('setuptools')
        requires = dist.requires()
        
        assert isinstance(requires, list)
    
    def test_distribution_get_metadata(self):
        """Test getting metadata from distribution."""
        dist = get_distribution('setuptools')
        
        # This might return empty string if metadata not available
        # but should not raise an error
        metadata_text = dist.get_metadata('PKG-INFO')
        assert isinstance(metadata_text, str)


class TestVersionParsing:
    """Tests for version parsing and comparison."""
    
    def test_simple_versions(self):
        """Test parsing simple version numbers."""
        versions = ['1.0.0', '1.0.1', '1.1.0', '2.0.0']
        parsed = [parse_version(v) for v in versions]
        
        # Check ordering
        for i in range(len(parsed) - 1):
            assert parsed[i] < parsed[i + 1]
    
    def test_prerelease_versions(self):
        """Test that pre-release versions sort correctly."""
        v_stable = parse_version('1.0.0')
        v_alpha = parse_version('1.0.0a1')
        v_beta = parse_version('1.0.0b1')
        
        # Stable should be greater than pre-releases
        assert v_stable > v_alpha
        assert v_stable > v_beta
        assert v_beta > v_alpha
    
    def test_version_equality(self):
        """Test version equality."""
        v1 = parse_version('1.0.0')
        v2 = parse_version('1.0.0')
        v3 = parse_version('1.0.1')
        
        assert v1 == v2
        assert v1 != v3


class TestEntryPoints:
    """Tests for entry point functionality."""
    
    def test_entry_point_has_attributes(self):
        """Test entry points have required attributes."""
        scripts = list(iter_entry_points('console_scripts'))
        
        if scripts:  # Only test if console scripts exist
            ep = scripts[0]
            assert hasattr(ep, 'name')
            assert hasattr(ep, 'module_name')
    
    def test_filter_entry_points_by_name(self):
        """Test filtering entry points by name."""
        # Get all console scripts
        all_scripts = list(iter_entry_points('console_scripts'))
        
        if all_scripts:
            # Pick a name and filter by it
            test_name = all_scripts[0].name
            filtered = list(iter_entry_points('console_scripts', name=test_name))
            
            assert len(filtered) >= 1
            assert all(ep.name == test_name for ep in filtered)


class TestDistributionWrapper:
    """Tests for DistributionWrapper class."""
    
    def test_wrapper_string_representation(self):
        """Test wrapper has string representation."""
        dist = get_distribution('setuptools')
        repr_str = repr(dist)
        
        assert 'DistributionWrapper' in repr_str
        assert 'setuptools' in repr_str.lower()
    
    def test_has_version_property(self):
        """Test has_version property."""
        dist = get_distribution('setuptools')
        
        assert dist.has_version is True
        assert isinstance(dist.version, str)
    
    def test_parsed_version_property(self):
        """Test parsed_version property."""
        dist = get_distribution('setuptools')
        parsed = dist.parsed_version
        
        assert parsed is not None
        # Should be comparable
        assert parsed == parse_version(dist.version)
    
    def test_as_requirement(self):
        """Test as_requirement method."""
        dist = get_distribution('setuptools')
        req = dist.as_requirement()
        
        assert isinstance(req, str)
        assert 'setuptools' in req.lower()
        assert '==' in req
        assert dist.version in req


# Pytest fixtures for common test data
@pytest.fixture
def sample_metadata():
    """Sample metadata for testing."""
    return """Metadata-Version: 1.2
Name: sample-package
Version: 1.0.0
Summary: A sample package for testing
Home-page: https://example.com
Author: Test Author
Author-email: test@example.com
License: MIT
Classifier: Development Status :: 4 - Beta
Classifier: Intended Audience :: Developers
Classifier: License :: OSI Approved :: MIT License
"""


@pytest.fixture
def minimal_metadata():
    """Minimal valid metadata."""
    return """Name: minimal-package
Version: 0.1.0
"""


class TestMetadataFixtures:
    """Tests using fixtures."""
    
    def test_sample_metadata_parsing(self, sample_metadata):
        """Test parsing sample metadata."""
        parsed, known_keys = metadata.parse_metadata(sample_metadata)
        
        assert parsed['Name'] == 'sample-package'
        assert parsed['Version'] == '1.0.0'
        assert 'Author' in parsed
        assert 'Classifier' in parsed
    
    def test_minimal_metadata_parsing(self, minimal_metadata):
        """Test parsing minimal metadata."""
        parsed, known_keys = metadata.parse_metadata(minimal_metadata)
        
        assert parsed['Name'] == 'minimal-package'
        assert parsed['Version'] == '0.1.0'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
