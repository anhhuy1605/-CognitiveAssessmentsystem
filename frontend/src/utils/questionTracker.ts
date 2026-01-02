/**
 * Question Tracker Utility
 * Tracks current active question for conditional rendering
 */

export interface QuestionInfo {
  questionId: string;
  questionCategory: string;
  domain?: string;
  displayMode?: string;
  hiddenContent?: string[];
  index?: number;
}

/**
 * Extract current question from messages
 */
export function getCurrentQuestion(
  messages: Array<{
    type?: string;
    questionId?: string;
    questionCategory?: string;
    domain?: string;
    displayMode?: string;
    hiddenContent?: string[];
  }>
): QuestionInfo | null {
  // Get last bot message with question info
  const lastBotMessage = messages
    .slice()
    .reverse()
    .find(m => m.type === 'bot' && m.questionId && m.questionCategory);

  if (!lastBotMessage || !lastBotMessage.questionId) {
    return null;
  }

  return {
    questionId: lastBotMessage.questionId,
    questionCategory: lastBotMessage.questionCategory!,
    domain: lastBotMessage.domain,
    displayMode: lastBotMessage.displayMode,
    hiddenContent: lastBotMessage.hiddenContent,
    index: messages.length - 1,
  };
}

/**
 * Check if question is currently active
 */
export function isQuestionActive(
  questionId: string,
  currentQuestion: QuestionInfo | null
): boolean {
  return currentQuestion?.questionId === questionId;
}

/**
 * Get question by ID from messages
 */
export function getQuestionById(
  questionId: string,
  messages: Array<{ questionId?: string; [key: string]: any }>
): any | null {
  return messages.find(m => m.questionId === questionId) || null;
}

