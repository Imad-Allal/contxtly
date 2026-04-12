export interface ContextTranslation {
  source: string;
  target: string;
}

export interface TranslationData {
  translation?: string;
  meaning?: string;
  breakdown?: string;
  context_translation?: ContextTranslation;
  collocation_pattern?: string;
  related_words?: Array<{ text: string }>;
  word_type?: string;
}

export interface Word {
  id?: string;
  text: string;
  lemma?: string;
  translation: TranslationData | string;
  url?: string;
  timestamp?: number;
}


export type TranslationDetail =
  | { label: string; color: string; text: string; source?: undefined }
  | { label: string; color: string; source: string; target: string; text?: undefined };
