import type { Word } from "./types";

export const LANGUAGES = [
  { code: "en", label: "🇬🇧 English" },
  { code: "es", label: "\u{1F1EA}\u{1F1F8} Spanish" },
  { code: "fr", label: "\u{1F1EB}\u{1F1F7} French" },
  { code: "de", label: "\u{1F1E9}\u{1F1EA} German" },
  { code: "it", label: "\u{1F1EE}\u{1F1F9} Italian" },
  { code: "pt", label: "\u{1F1F5}\u{1F1F9} Portuguese" },
  { code: "zh", label: "\u{1F1E8}\u{1F1F3} Chinese" },
  { code: "ja", label: "\u{1F1EF}\u{1F1F5} Japanese" },
  { code: "ko", label: "\u{1F1F0}\u{1F1F7} Korean" },
  { code: "ar", label: "\u{1F1F8}\u{1F1E6} Arabic" },
  { code: "ru", label: "\u{1F1F7}\u{1F1FA} Russian" },
];

export const MOCK_WORDS: Word[] = [
  {
    text: "strittige",
    lemma: "strittig",
    translation: {
      translation: "controversial, disputed",
      meaning: "Describes something that is subject to debate or disagreement among people",
      breakdown: "streit (dispute) + -ig (adj. suffix) + -e (inflection)",
      context_translation: {
        source: "Das ist ein strittiges Thema in der Politik.",
        target: "This is a controversial topic in politics.",
      },
    },
    url: "https://example.com/article",
    timestamp: Date.now() - 3600000,
  },
  {
    text: "Zusammenhang",
    lemma: "Zusammenhang",
    translation: {
      translation: "context, connection, correlation",
      meaning: "The relationship or connection between things; the context in which something occurs",
      breakdown: 'zusammen (together) + hang (connection) \u2192 "hanging together"',
    },
    url: "https://example.com/article2",
    timestamp: Date.now() - 7200000,
  },
  {
    text: "bonjour",
    lemma: "bonjour",
    translation: {
      translation: "hello, good morning",
      meaning: "A common French greeting used at the start of the day",
      breakdown: 'bon (good) + jour (day) \u2192 "good day"',
    },
    url: "https://example.com/french",
    timestamp: Date.now() - 86400000,
  },
  {
    text: "\u00E9panouissement",
    lemma: "\u00E9panouissement",
    translation: {
      translation: "blossoming, flourishing, fulfillment",
      meaning: "The process of developing fully and thriving; personal or creative fulfillment",
      breakdown: "\u00E9panouir (to blossom) + -ment (noun suffix)",
      context_translation: {
        source: "Son \u00E9panouissement personnel est remarquable.",
        target: "His personal fulfillment is remarkable.",
      },
    },
    url: "https://example.com/french2",
    timestamp: Date.now() - 172800000,
  },
];
