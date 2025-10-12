"""
Language management for backend
"""

from .en import TRANSLATIONS as EN_TRANSLATIONS
from .vi import TRANSLATIONS as VI_TRANSLATIONS

class LanguageManager:
    """Manages language translations"""
    
    def __init__(self, default_language='vi'):
        self.default_language = default_language
        self.translations = {
            'en': EN_TRANSLATIONS,
            'vi': VI_TRANSLATIONS
        }
    
    def get_text(self, key: str, language: str = None) -> str:
        """Get translated text for a key"""
        if language is None:
            language = self.default_language
        
        if language not in self.translations:
            language = self.default_language
        
        return self.translations[language].get(key, key)
    
    def get_available_languages(self) -> list:
        """Get list of available languages"""
        return list(self.translations.keys())
    
    def set_default_language(self, language: str):
        """Set default language"""
        if language in self.translations:
            self.default_language = language

# Global language manager instance
language_manager = LanguageManager()

def t(key: str, language: str = None) -> str:
    """Shortcut function to get translated text"""
    return language_manager.get_text(key, language)
