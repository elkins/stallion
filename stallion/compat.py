"""
Compatibility layer for Stallion.
Makes modern Python packaging work with legacy Stallion templates and code.
"""
import sys
from typing import Any, Dict, List, Optional, Iterator

try:
    from importlib import metadata
except ImportError:
    try:
        import importlib_metadata as metadata
    except ImportError:
        import pkg_resources as metadata

from packaging import version


class DistributionWrapper:
    """
    Makes modern importlib.metadata Distribution objects behave exactly
    like legacy pkg_resources Distribution objects.
    """

    def __init__(self, modern_dist):
        self._dist = modern_dist

        # Map all legacy attributes
        self.project_name = getattr(modern_dist, 'project_name', getattr(modern_dist, 'name', ''))
        self.version = getattr(modern_dist, 'version', '')
        self.location = getattr(modern_dist, 'location', '')
        self.key = self.project_name.lower()  # Legacy attribute
        self.egg_name = self.project_name  # Legacy attribute

        # These might not exist in modern distributions, but templates expect them
        self.py_version = '3'  # Default value
        self.precedence = 0  # Default value

    def __getattr__(self, name):
        """Delegate any unknown attributes to the underlying distribution"""
        return getattr(self._dist, name)

    def __repr__(self):
        return f"<DistributionWrapper {self.project_name} {self.version}>"

    def get_entry_map(self, group=None):
        """
        Legacy method: get entry points mapping.
        Matches pkg_resources.Distribution.get_entry_map() exactly.
        """
        entry_map = {}

        for ep in getattr(self._dist, 'entry_points', []):
            ep_group = getattr(ep, 'group', 'unknown')

            if ep_group not in entry_map:
                entry_map[ep_group] = {}

            # Create a wrapper that makes EntryPoint look legacy too
            entry_map[ep_group][ep.name] = EntryPointWrapper(ep)

        # If a specific group was requested, return just that group
        if group is not None:
            return entry_map.get(group, {})

        return entry_map

    def get_metadata(self, name):
        """
        Legacy method: get metadata by field name.
        Matches pkg_resources.Distribution.get_metadata().
        """
        if hasattr(self._dist.metadata, 'get'):
            return self._dist.metadata.get(name, '')
        return ''

    def get_metadata_lines(self, name):
        """
        Legacy method: get metadata lines for multi-value fields.
        Matches pkg_resources.Distribution.get_metadata_lines().
        """
        if hasattr(self._dist.metadata, 'get_all'):
            return self._dist.metadata.get_all(name, [])

        # Fallback: try to split single string
        value = self.get_metadata(name)
        if value:
            return [line.strip() for line in value.split('\n') if line.strip()]

        return []

    def as_requirement(self) -> str:
        """Legacy method: return requirement string.
        
        :return: Requirement string like 'package==1.0.0'
        """
        return f"{self.project_name}=={self.version}"

    def requires(self, extras: Optional[List[str]] = None) -> List[str]:
        """Legacy method: get requirements.
        
        :param extras: Optional list of extras to include
        :return: List of requirement strings
        """
        if hasattr(self._dist, 'requires') and self._dist.requires:
            return [str(req) for req in self._dist.requires]
        return []

    @property
    def has_version(self) -> bool:
        """Legacy property: check if version exists.
        
        :return: True if version is set, False otherwise
        """
        return bool(self.version)

    @property
    def parsed_version(self) -> Any:
        """Legacy property: parsed version object.
        
        :return: Parsed version object supporting comparisons
        """
        try:
            return version.parse(self.version)
        except:
            class FallbackVersion:
                def __init__(self, vstr): self.vstr = vstr

                def __str__(self): return self.vstr

            return FallbackVersion(self.version)


class EntryPointWrapper:
    """Makes modern EntryPoint objects behave like legacy ones.
    
    Provides backward compatibility for entry point access patterns
    used by Stallion.
    """

    def __init__(self, modern_ep: Any) -> None:
        """Initialize wrapper around a modern entry point.
        
        :param modern_ep: An EntryPoint object from importlib.metadata
        """
        self._ep = modern_ep
        self.name = getattr(modern_ep, 'name', '')
        self.module_name = getattr(modern_ep, 'module', '')
        self.attrs = getattr(modern_ep, 'attr', '').split('.') if getattr(modern_ep, 'attr', '') else []
        self.extras = getattr(modern_ep, 'extras', [])
        self.dist = None  # Will be set by calling code if needed

    def __getattr__(self, name):
        return getattr(self._ep, name)

    def load(self, require: bool = True, *args: Any, **kwargs: Any) -> Optional[Any]:
        """Legacy method: load the entry point.
        
        :param require: Whether to require dependencies (ignored)
        :return: The loaded entry point object or None on error
        """
        try:
            return self._ep.load()
        except Exception as e:
            print(f"DEBUG: Error loading entry point {self.name}: {e}")
            return None


class WorkingSetWrapper:
    """Makes the working set of distributions compatible.
    
    Provides a lazy-loading wrapper around the set of all installed
    Python distributions, with legacy API compatibility.
    """

    def __init__(self) -> None:
        """Initialize an empty working set wrapper."""
        self._distributions = None
        self._by_key = {}

    def __iter__(self) -> Iterator[DistributionWrapper]:
        return iter(self._get_distributions())

    def __len__(self) -> int:
        return len(self._get_distributions())

    def _get_distributions(self) -> List[DistributionWrapper]:
        """Get all distributions, loading them if necessary.
        
        :return: List of wrapped distribution objects
        """
        if self._distributions is None:
            self._distributions = []
            self._by_key = {}

            try:
                raw_dists = list(metadata.distributions())
            except AttributeError:
                # pkg_resources fallback
                if hasattr(metadata, 'working_set'):
                    raw_dists = list(metadata.working_set)
                else:
                    raw_dists = []

            for dist in raw_dists:
                wrapped = DistributionWrapper(dist)
                self._distributions.append(wrapped)
                self._by_key[wrapped.key] = wrapped

        return self._distributions

    def __getitem__(self, key: str) -> DistributionWrapper:
        """Get distribution by key (lowercase name).
        
        :param key: Distribution key (lowercase name)
        :return: Wrapped distribution object
        :raises KeyError: If distribution not found
        """
        self._get_distributions()  # Ensure loaded
        return self._by_key[key]

    def find(self, req: str) -> Optional[DistributionWrapper]:
        """Legacy method: find distribution by requirement.
        
        :param req: Package name or requirement string
        :return: Distribution if found, None otherwise
        """
        self._get_distributions()
        # Simple implementation - could be enhanced
        for dist in self._distributions:
            if dist.project_name == req:
                return dist
        return None


# Global working set instance
working_set: WorkingSetWrapper = WorkingSetWrapper()


def get_distribution(name: str) -> DistributionWrapper:
    """Get a distribution with full legacy compatibility.
    
    :param name: Package name (case-insensitive)
    :return: Wrapped distribution object
    :raises: PackageNotFoundError if distribution not found
    """
    try:
        raw_dist = metadata.distribution(name)
    except metadata.PackageNotFoundError:
        # Try case-insensitive search
        for dist in working_set:
            if dist.project_name.lower() == name.lower():
                return dist
        raise
    except AttributeError:
        # pkg_resources fallback
        if hasattr(metadata, 'get_distribution'):
            raw_dist = metadata.get_distribution(name)
        else:
            raise

    return DistributionWrapper(raw_dist)


def iter_entry_points(group: Optional[str] = None, name: Optional[str] = None) -> List[EntryPointWrapper]:
    """Legacy-compatible entry point iterator.
    
    :param group: Optional group name to filter by (e.g., 'console_scripts')
    :param name: Optional entry point name to filter by
    :return: List of wrapped entry point objects
    """
    results = []

    for dist in working_set:
        entry_map = dist.get_entry_map()

        if group is None:
            # All entry points from all groups
            for group_name, entries in entry_map.items():
                for ep_name, ep in entries.items():
                    if name is None or ep_name == name:
                        results.append(ep)
        else:
            # Specific group
            entries = entry_map.get(group, {})
            for ep_name, ep in entries.items():
                if name is None or ep_name == name:
                    results.append(ep)

    return results


def parse_version(version_string: str) -> Any:
    """Legacy-compatible version parsing.
    
    :param version_string: Version string to parse (e.g., '1.2.3')
    :return: Parsed version object that supports comparison
    """
    try:
        return version.parse(version_string)
    except:
        class FallbackVersion:
            def __init__(self, vstr): self.vstr = vstr

            def __str__(self): return self.vstr

            def __lt__(self, other): return self.vstr < other.vstr

            def __gt__(self, other): return self.vstr > other.vstr

            def __eq__(self, other): return self.vstr == other.vstr

        return FallbackVersion(version_string)
