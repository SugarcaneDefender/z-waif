# API package initialization
# This makes all API modules importable

# Import all modules to make them available when importing API
from . import api_controller
from . import fallback_api
from . import Oogabooga_Api_Support
from . import oobaooga_api
from . import character_card
from . import ollama_api
from . import task_profiles

# Make all modules available for import
__all__ = [
    'api_controller',
    'fallback_api',
    'Oogabooga_Api_Support',
    'oobaooga_api',
    'character_card',
    'ollama_api',
    'task_profiles'
] 