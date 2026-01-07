/**
 * Vietnamese Utilities - Helper functions for Vietnamese text processing
 */

/**
 * Parse Vietnamese letter from text
 * Handles Vietnamese diacritics and special characters
 */
export function parseVietnameseLetter(text: string): string[] {
  if (!text) return [];
  
  // Normalize Vietnamese text
  const normalized = text.normalize('NFD');
  
  // Split into characters, preserving Vietnamese letters
  const letters: string[] = [];
  for (let i = 0; i < normalized.length; i++) {
    const char = normalized[i];
    // Skip combining diacritical marks (they'll be part of the previous character)
    if (char >= '\u0300' && char <= '\u036F') {
      continue;
    }
    // Collect base character and any following diacritics
    let letter = char;
    let j = i + 1;
    while (j < normalized.length && normalized[j] >= '\u0300' && normalized[j] <= '\u036F') {
      letter += normalized[j];
      j++;
    }
    if (letter.trim()) {
      letters.push(letter);
    }
    i = j - 1;
  }
  
  return letters.length > 0 ? letters : text.split('');
}

/**
 * Remove Vietnamese diacritics
 */
export function removeDiacritics(text: string): string {
  return text
    .normalize('NFD')
    .replace(/[\u0300-\u036F]/g, '')
    .normalize('NFC');
}

/**
 * Check if character is Vietnamese letter
 */
export function isVietnameseLetter(char: string): boolean {
  const vietnameseRanges = [
    /[àáạảãâầấậẩẫăằắặẳẵ]/i,
    /[èéẹẻẽêềếệểễ]/i,
    /[ìíịỉĩ]/i,
    /[òóọỏõôồốộổỗơờớợởỡ]/i,
    /[ùúụủũưừứựửữ]/i,
    /[ỳýỵỷỹ]/i,
    /[đ]/i,
  ];
  
  return vietnameseRanges.some(regex => regex.test(char)) || /[a-z]/i.test(char);
}

/**
 * Parse Vietnamese number from text
 * Extracts numbers from Vietnamese text (e.g., "chín mươi ba" -> 93)
 */
export function parseVietnameseNumber(text: string): number[] {
  if (!text) return [];
  
  // Extract all numbers (digits)
  const numbers = text.match(/\d+/g);
  if (numbers) {
    return numbers.map(n => parseInt(n, 10));
  }
  
  // Try to parse Vietnamese number words
  const vietnameseNumbers: Record<string, number> = {
    'không': 0, 'một': 1, 'hai': 2, 'ba': 3, 'bốn': 4, 'năm': 5,
    'sáu': 6, 'bảy': 7, 'tám': 8, 'chín': 9, 'mười': 10,
    'mười một': 11, 'mười hai': 12, 'mười ba': 13, 'mười bốn': 14,
    'mười lăm': 15, 'mười sáu': 16, 'mười bảy': 17, 'mười tám': 18,
    'mười chín': 19, 'hai mươi': 20, 'ba mươi': 30, 'bốn mươi': 40,
    'năm mươi': 50, 'sáu mươi': 60, 'bảy mươi': 70, 'tám mươi': 80,
    'chín mươi': 90, 'một trăm': 100,
  };
  
  const lowerText = text.toLowerCase().trim();
  if (vietnameseNumbers[lowerText] !== undefined) {
    return [vietnameseNumbers[lowerText]];
  }
  
  // Try compound numbers (e.g., "chín mươi ba")
  for (const [word, num] of Object.entries(vietnameseNumbers)) {
    if (lowerText.includes(word)) {
      // Simple extraction - in production, use proper NLP
      const match = lowerText.match(new RegExp(word.replace(/\s+/g, '\\s+'), 'i'));
      if (match) {
        return [num];
      }
    }
  }
  
  return [];
}

/**
 * Extract keywords from text
 * Removes common words and extracts meaningful keywords
 */
export function extractKeywords(text: string): string[] {
  if (!text) return [];
  
  const stopWords = new Set([
    'và', 'của', 'cho', 'với', 'từ', 'trong', 'trên', 'dưới', 'sau', 'trước',
    'là', 'có', 'được', 'bị', 'mà', 'nếu', 'thì', 'khi', 'để', 'vì', 'do',
    'một', 'hai', 'ba', 'bốn', 'năm', 'sáu', 'bảy', 'tám', 'chín', 'mười',
    'cái', 'con', 'chiếc', 'bạn', 'tôi', 'ông', 'bà', 'anh', 'chị', 'em',
  ]);
  
  const words = text
    .toLowerCase()
    .replace(/[^\w\sàáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ]/g, ' ')
    .split(/\s+/)
    .filter(word => word.length > 1 && !stopWords.has(word));
  
  return [...new Set(words)]; // Remove duplicates
}

/**
 * Match keywords between two texts
 * Returns similarity score (0-1) and matched keywords
 */
export function matchKeywords(text1: string, text2: string): { score: number; matched: string[] } {
  const keywords1 = extractKeywords(text1);
  const keywords2 = extractKeywords(text2);
  
  if (keywords1.length === 0 || keywords2.length === 0) {
    return { score: 0, matched: [] };
  }
  
  const matched = keywords1.filter(kw => keywords2.includes(kw));
  const score = matched.length / Math.max(keywords1.length, keywords2.length);
  
  return { score, matched };
}

