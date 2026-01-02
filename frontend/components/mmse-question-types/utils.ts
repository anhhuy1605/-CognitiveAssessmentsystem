/**
 * Utility functions for MMSE question type components
 */

/**
 * Parse Vietnamese number words to number
 * Example: "chín mươi ba" → 93, "tám mươi sáu" → 86
 */
export function parseVietnameseNumber(text: string): number | null {
  const normalized = text.toLowerCase().trim();
  
  // Direct number match (digits)
  const digitMatch = normalized.match(/\d+/);
  if (digitMatch) {
    return parseInt(digitMatch[0], 10);
  }
  
  // Vietnamese number words mapping
  const numberMap: Record<string, number> = {
    'không': 0, 'một': 1, 'hai': 2, 'ba': 3, 'bốn': 4, 'năm': 5,
    'sáu': 6, 'bảy': 7, 'tám': 8, 'chín': 9, 'mười': 10,
    'mười một': 11, 'mười hai': 12, 'mười ba': 13, 'mười bốn': 14, 'mười lăm': 15,
    'mười sáu': 16, 'mười bảy': 17, 'mười tám': 18, 'mười chín': 19,
    'hai mươi': 20, 'ba mươi': 30, 'bốn mươi': 40, 'năm mươi': 50,
    'sáu mươi': 60, 'bảy mươi': 70, 'tám mươi': 80, 'chín mươi': 90,
    'một trăm': 100
  };
  
  // Check for direct match
  if (numberMap[normalized]) {
    return numberMap[normalized];
  }
  
  // Handle compound numbers (e.g., "chín mươi ba" = 93)
  const tensPattern = /(chín|tám|bảy|sáu|năm|bốn|ba|hai|một)\s*mươi\s*(một|hai|ba|bốn|lăm|sáu|bảy|tám|chín)?/;
  const match = normalized.match(tensPattern);
  
  if (match) {
    const tensWord = match[1];
    const onesWord = match[2];
    const tensValue: Record<string, number> = {
      'một': 10, 'hai': 20, 'ba': 30, 'bốn': 40, 'năm': 50,
      'sáu': 60, 'bảy': 70, 'tám': 80, 'chín': 90
    };
    const onesValue: Record<string, number> = {
      'một': 1, 'hai': 2, 'ba': 3, 'bốn': 4, 'lăm': 5,
      'sáu': 6, 'bảy': 7, 'tám': 8, 'chín': 9
    };
    
    const tens = tensValue[tensWord] || 0;
    const ones = onesWord ? (onesValue[onesWord] || 0) : 0;
    return tens + ones;
  }
  
  return null;
}

/**
 * Extract keywords from words with classifiers
 * Example: ["Con mèo", "Chiếc xe", "Cây lúa"] → ["mèo", "xe", "lúa"]
 */
export function extractKeywords(words: string[]): string[] {
  return words.map(word => {
    // Remove common Vietnamese classifiers
    const classifiers = ['con', 'chiếc', 'cây', 'quả', 'cái', 'bức', 'tờ', 'bài', 'cuốn'];
    const parts = word.toLowerCase().split(/\s+/);
    
    // Remove classifier (first word if it's a classifier)
    if (parts.length > 1 && classifiers.includes(parts[0])) {
      return parts.slice(1).join(' ');
    }
    
    return parts.join(' ');
  });
}

/**
 * Match keywords in transcript (fuzzy matching with accents)
 */
export function matchKeywords(transcript: string, keywords: string[]): string[] {
  const normalized = transcript.toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '') // Remove accents
    .replace(/[.,!?;:]/g, ' '); // Remove punctuation
  
  const matched: string[] = [];
  
  for (const keyword of keywords) {
    const normalizedKeyword = keyword.toLowerCase()
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '');
    
    // Check if keyword appears in transcript (word boundary or partial)
    const regex = new RegExp(`\\b${normalizedKeyword.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}`, 'i');
    if (regex.test(normalized) || normalized.includes(normalizedKeyword)) {
      matched.push(keyword);
    }
  }
  
  return matched;
}

/**
 * Parse Vietnamese letter name to letter
 * Example: "hờ" → "H", "nờ" → "N", "i ngắn" → "Ị"
 */
export function parseVietnameseLetter(letterName: string): string | null {
  const normalized = letterName.toLowerCase().trim();
  
  // Direct letter match
  if (/^[a-zàáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ]$/i.test(normalized)) {
    return normalized.toUpperCase();
  }
  
  // Vietnamese letter names
  const letterMap: Record<string, string> = {
    'a': 'A', 'á': 'Á', 'à': 'À', 'ả': 'Ả', 'ã': 'Ã', 'ạ': 'Ạ',
    'ă': 'Ă', 'ắ': 'Ắ', 'ằ': 'Ằ', 'ẳ': 'Ẳ', 'ẵ': 'Ẵ', 'ặ': 'Ặ',
    'â': 'Â', 'ấ': 'Ấ', 'ầ': 'Ầ', 'ẩ': 'Ẩ', 'ẫ': 'Ẫ', 'ậ': 'Ậ',
    'b': 'B', 'bê': 'B',
    'c': 'C', 'xê': 'C', 'cê': 'C',
    'd': 'D', 'dê': 'D',
    'đ': 'Đ', 'đê': 'Đ',
    'e': 'E', 'é': 'É', 'è': 'È', 'ẻ': 'Ẻ', 'ẽ': 'Ẽ', 'ẹ': 'Ẹ',
    'ê': 'Ê', 'ế': 'Ế', 'ề': 'Ề', 'ể': 'Ể', 'ễ': 'Ễ', 'ệ': 'Ệ',
    'g': 'G', 'giê': 'G',
    'h': 'H', 'hờ': 'H', 'hát': 'H',
    'i': 'I', 'i ngắn': 'I',
    'í': 'Í', 'ì': 'Ì', 'ỉ': 'Ỉ', 'ĩ': 'Ĩ', 'ị': 'Ị',
    'k': 'K', 'ca': 'K',
    'l': 'L', 'e-lờ': 'L', 'lờ': 'L',
    'm': 'M', 'em-mờ': 'M', 'mờ': 'M',
    'n': 'N', 'en-nờ': 'N', 'nờ': 'N',
    'o': 'O', 'ó': 'Ó', 'ò': 'Ò', 'ỏ': 'Ỏ', 'õ': 'Õ', 'ọ': 'Ọ',
    'ô': 'Ô', 'ố': 'Ố', 'ồ': 'Ồ', 'ổ': 'Ổ', 'ỗ': 'Ỗ', 'ộ': 'Ộ',
    'ơ': 'Ơ', 'ớ': 'Ớ', 'ờ': 'Ờ', 'ở': 'Ở', 'ỡ': 'Ỡ', 'ợ': 'Ợ',
    'p': 'P', 'pê': 'P',
    'q': 'Q', 'quy': 'Q', 'cu': 'Q',
    'r': 'R', 'e-rờ': 'R', 'rờ': 'R',
    's': 'S', 'ét-sì': 'S', 'sờ': 'S',
    't': 'T', 'tê': 'T', 'tờ': 'T',
    'u': 'U', 'ú': 'Ú', 'ù': 'Ù', 'ủ': 'Ủ', 'ũ': 'Ũ', 'ụ': 'Ụ',
    'ư': 'Ư', 'ứ': 'Ứ', 'ừ': 'Ừ', 'ử': 'Ử', 'ữ': 'Ữ', 'ự': 'Ự',
    'v': 'V', 'vê': 'V', 'vờ': 'V',
    'x': 'X', 'ích-xì': 'X', 'xờ': 'X',
    'y': 'Y', 'y dài': 'Y', 'i dài': 'Y',
    'ý': 'Ý', 'ỳ': 'Ỳ', 'ỷ': 'Ỷ', 'ỹ': 'Ỹ', 'ỵ': 'Ỵ'
  };
  
  return letterMap[normalized] || null;
}

/**
 * Check if text contains stop keywords
 */
export function containsStopKeyword(text: string): boolean {
  const stopKeywords = ['dừng', 'dừng lại', 'thôi', 'hết rồi', 'không làm nữa', 'stop', 'end'];
  const normalized = text.toLowerCase();
  return stopKeywords.some(keyword => normalized.includes(keyword));
}

