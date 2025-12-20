'use client';

 
const translations: Record<Language, Record<string, string>> = {
  vi: {
    // Menu
    home: 'Trang chủ',
    assessment: 'Đánh giá',
    memory_test: 'Đánh giá nhận thức',
    memory_test_desc: 'Bài kiểm tra giọng nói hỗ trợ sàng lọc MMSE',
    statistics: 'Kết quả',
    statistics_desc: 'Theo dõi tiến độ và kết quả đánh giá',
    information: 'Giới thiệu',
    information_desc: 'Toàn bộ các thông tin về dự án Cá Vàng',
    profile: 'Hồ sơ',
    profile_desc: 'Thông tin cá nhân và cài đặt tài khoản',
    settings: 'Cài đặt',
    settings_desc: 'Tuỳ chỉnh ngôn ngữ, âm thanh và quyền riêng tư',
    about: 'Giới thiệu',
    news_research: 'tin tức và nghiên cứu',

    // Cognitive assessment
    cognitive_assessment: 'Đánh giá nhận thức',
    results: 'Kết quả',
    app_title: 'Cá Vàng',

    // Progress status
    memory_good: 'Trí nhớ tốt',
    needs_monitoring: 'Cần theo dõi',
    needs_intervention: 'Cần can thiệp',
    needs_special_evaluation: 'Cần đánh giá chuyên sâu',
  },
  en: {
    // Menu
    home: 'Home',
    assessment: 'Assessment',
    memory_test: 'Cognitive Assessment',
    memory_test_desc: 'Voice-based screening to support MMSE',
    statistics: 'Statistics',
    statistics_desc: 'Track progress and assessment results',
    information: 'Information',
    information_desc: 'User guide and health knowledge',
    profile: 'Profile',
    profile_desc: 'Personal information and account settings',
    settings: 'Settings',
    settings_desc: 'Customize language, audio and privacy',

    about: 'About',
    news_research: 'News & Research',

    // Cognitive assessment
    cognitive_assessment: 'Cognitive Assessment',
    results: 'Results',
    app_title: 'Cá Vàng',

    memory_good: 'Good memory',
    needs_monitoring: 'Needs monitoring',
    needs_intervention: 'Needs intervention',
    needs_special_evaluation: 'Needs specialist evaluation',
  },
};

 

export const languages = {
  vi: 'Tiếng Việt',
  en: 'English',
} as const

export type LanguageCode = keyof typeof languages
export type Language = LanguageCode

export const defaultLanguage: LanguageCode = 'vi'

export function getTranslation(key: string, language: string = defaultLanguage): string {
  const lang = (language in translations ? language : defaultLanguage) as keyof typeof translations
  return translations[lang]?.[key] || key
}

export function getAvailableLanguages(): { code: LanguageCode; name: string }[] {
  return Object.entries(languages).map(([code, name]) => ({
    code: code as LanguageCode,
    name
  }))
}

export function isValidLanguage(code: string): code is LanguageCode {
  return code in languages
}


