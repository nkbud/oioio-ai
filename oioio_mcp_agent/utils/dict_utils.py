"""
Dictionary utility functions.
"""

from typing import Any, Dict


def deep_merge(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recursively merge two dictionaries.
    
    Values in dict2 override values in dict1. If both values are dictionaries,
    they are merged recursively.
    
    Args:
        dict1: Base dictionary
        dict2: Dictionary to merge on top of base
        
    Returns:
        Merged dictionary
    """
    result = dict1.copy()
    
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    
    return result