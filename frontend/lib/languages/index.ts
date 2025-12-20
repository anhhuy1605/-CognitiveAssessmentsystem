import { en } from './en';
import { vi } from './vi';

export type Language = 'en' | 'vi';

export const languages = {
  en,
  vi,
} as const;

export type TranslationKey = keyof typeof en;

export function getTranslation(key: TranslationKey, language: Language = 'vi'): string {
  const translations = languages[language];
  const value = translations[key];
  return Array.isArray(value) ? value.join(', ') : (value || key);
}

export function getAvailableLanguages(): Language[] {
  return Object.keys(languages) as Language[];
}

export function isValidLanguage(language: string): language is Language {
  return language in languages;
}

