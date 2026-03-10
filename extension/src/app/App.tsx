import {
  useState,
  useEffect,
  useRef,
  useCallback,
  useMemo,
} from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Languages,
  Settings,
  Search,
  X,
  Layers,
  Square,
  CheckSquare,
  Trash2,
  ChevronDown,
  ExternalLink,
  BookOpen,
  Sparkles,
} from "lucide-react";

// ─────────────────────────────── Types ──────────────────────────────────────

interface ContextTranslation {
  source: string;
  target: string;
}

interface TranslationData {
  translation?: string;
  meaning?: string;
  breakdown?: string;
  context_translation?: ContextTranslation;
  collocation_pattern?: string;
  related_words?: Array<{ text: string }>;
  word_type?: string;
}

interface Word {
  text: string;
  lemma?: string;
  translation: TranslationData | string;
  url?: string;
  timestamp?: number;
}

// ───────────────────────────── Constants ─────────────────────────────────────

const LANGUAGES = [
  { code: "en", label: "English" },
  { code: "es", label: "🇪🇸 Spanish" },
  { code: "fr", label: "🇫🇷 French" },
  { code: "de", label: "🇩🇪 German" },
  { code: "it", label: "🇮🇹 Italian" },
  { code: "pt", label: "🇵🇹 Portuguese" },
  { code: "zh", label: "🇨🇳 Chinese" },
  { code: "ja", label: "🇯🇵 Japanese" },
  { code: "ko", label: "🇰🇷 Korean" },
  { code: "ar", label: "🇸🇦 Arabic" },
  { code: "ru", label: "🇷🇺 Russian" },
];

const MOCK_WORDS: Word[] = [
  {
    text: "strittige",
    lemma: "strittig",
    translation: {
      translation: "controversial, disputed",
      meaning:
        "Describes something that is subject to debate or disagreement among people",
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
      meaning:
        "The relationship or connection between things; the context in which something occurs",
      breakdown:
        'zusammen (together) + hang (connection) → "hanging together"',
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
      breakdown: 'bon (good) + jour (day) → "good day"',
    },
    url: "https://example.com/french",
    timestamp: Date.now() - 86400000,
  },
  {
    text: "épanouissement",
    lemma: "épanouissement",
    translation: {
      translation: "blossoming, flourishing, fulfillment",
      meaning:
        "The process of developing fully and thriving; personal or creative fulfillment",
      breakdown: "épanouir (to blossom) + -ment (noun suffix)",
      context_translation: {
        source: "Son épanouissement personnel est remarquable.",
        target: "His personal fulfillment is remarkable.",
      },
    },
    url: "https://example.com/french2",
    timestamp: Date.now() - 172800000,
  },
];

// ────────────────────────── Chrome API Helpers ───────────────────────────────

const isChromeExt =
  typeof chrome !== "undefined" && !!chrome?.runtime?.id;

async function chromeLoadWords(): Promise<Word[]> {
  if (!isChromeExt) return MOCK_WORDS;
  const { highlights = {} } = await chrome.storage.local.get("highlights");
  const seen = new Set<string>();
  const allWords = Object.entries(
    highlights as Record<string, Word[]>
  ).flatMap(([url, items]) => items.map((h) => ({ ...h, url })));
  return allWords
    .sort((a, b) => (b.timestamp || 0) - (a.timestamp || 0))
    .filter((h) => {
      const key = h.lemma || h.text;
      return !seen.has(key) && seen.add(key);
    });
}

async function chromeLoadSettings(): Promise<{
  targetLang: string;
  mode: string;
}> {
  if (!isChromeExt) return { targetLang: "en", mode: "smart" };
  return chrome.runtime.sendMessage({ action: "getSettings" });
}

function chromeSaveSettings(data: { targetLang: string; mode: string }) {
  if (!isChromeExt) return;
  chrome.runtime.sendMessage({ action: "saveSettings", data });
}

async function chromeDeleteWords(lemmas: string[]) {
  if (!isChromeExt) return;
  const { highlights = {} } = await chrome.storage.local.get("highlights");
  const h = highlights as Record<string, Word[]>;
  for (const url of Object.keys(h)) {
    h[url] = h[url].filter((w) => !lemmas.includes(w.lemma || w.text));
    if (!h[url].length) delete h[url];
  }
  await chrome.storage.local.set({ highlights: h });
  const tabs = await chrome.tabs.query({});
  for (const tab of tabs) {
    if (tab.id) {
      lemmas.forEach((lemma) =>
        chrome.tabs
          .sendMessage(tab.id!, { action: "removeHighlight", lemma })
          .catch(() => {})
      );
    }
  }
}

// ─────────────────────────── Background Orbs ────────────────────────────────

function BackgroundOrbs() {
  return (
    <div className="absolute inset-0 overflow-hidden pointer-events-none">
      <motion.div
        className="absolute w-80 h-80 rounded-full bg-blue-400/[0.07] blur-[64px]"
        animate={{
          x: [0, 28, -18, 0],
          y: [0, -18, 26, 0],
          scale: [1, 1.08, 0.93, 1],
        }}
        transition={{ duration: 9, repeat: Infinity, ease: "easeInOut" }}
        style={{ top: "-80px", left: "-70px" }}
      />
      <motion.div
        className="absolute w-72 h-72 rounded-full bg-slate-400/[0.07] blur-[64px]"
        animate={{
          x: [0, -22, 14, 0],
          y: [0, 18, -14, 0],
          scale: [1, 0.92, 1.08, 1],
        }}
        transition={{
          duration: 11,
          repeat: Infinity,
          ease: "easeInOut",
          delay: 2.5,
        }}
        style={{ top: "35%", right: "-55px" }}
      />
      <motion.div
        className="absolute w-64 h-64 rounded-full bg-indigo-400/[0.06] blur-[64px]"
        animate={{
          x: [0, 16, -24, 0],
          y: [0, 24, -10, 0],
          scale: [1, 1.05, 0.96, 1],
        }}
        transition={{
          duration: 13,
          repeat: Infinity,
          ease: "easeInOut",
          delay: 5,
        }}
        style={{ bottom: "-50px", left: "25%" }}
      />
    </div>
  );
}

// ─────────────────────────────── Word Card ───────────────────────────────────

interface WordCardProps {
  word: Word;
  index: number;
  isSelected: boolean;
  isExpanded: boolean;
  onToggleSelect: (key: string) => void;
  onToggleExpand: (key: string) => void;
  onOpenUrl: (url: string) => void;
}

function WordCard({
  word,
  index,
  isSelected,
  isExpanded,
  onToggleSelect,
  onToggleExpand,
  onOpenUrl,
}: WordCardProps) {
  const key = word.lemma || word.text;
  const t =
    typeof word.translation === "object" && word.translation !== null
      ? word.translation
      : null;
  const simpleTranslation =
    typeof word.translation === "string" ? word.translation : null;

  let displayWord = word.text;
  if (t?.collocation_pattern) {
    const parts = [word.text, ...(t.related_words || []).map((r) => r.text)];
    displayWord = `${parts.join("/")} (${t.collocation_pattern})`;
  } else if (word.lemma && word.text !== word.lemma) {
    displayWord = `${word.text} (${word.lemma})`;
  }

  type Detail =
    | { label: string; color: string; text: string; source?: undefined }
    | {
        label: string;
        color: string;
        source: string;
        target: string;
        text?: undefined;
      };

  // Map word_type → breakdown accent color
  const breakdownColor = (() => {
    const wt = t?.word_type;
    if (!wt) return t?.collocation_pattern ? "amber" : "slate";
    if (wt === "conjugated_verb" || wt === "separable_prefix") return "blue";
    if (wt === "noun" || wt === "plural_noun") return "violet";
    if (wt === "collocation_verb" || wt === "collocation_prep") return "amber";
    if (wt === "fixed_expression") return "rose";
    if (wt === "compound") return "emerald";
    return "slate";
  })();

  const details: Detail[] = [];
  if (t) {
    if (t.translation) details.push({ label: "Translation", color: "blue", text: t.translation });
    if (t.meaning) details.push({ label: "Meaning", color: "purple", text: t.meaning });
    if (t.breakdown) details.push({ label: "Breakdown", color: breakdownColor, text: t.breakdown });
    if (t.context_translation?.source) {
      details.push({
        label: "Context",
        color: "amber",
        source: t.context_translation.source,
        target: t.context_translation.target,
      });
    }
  } else if (simpleTranslation) {
    details.push({ label: "Translation", color: "blue", text: simpleTranslation });
  }

  const barMap: Record<string, string> = {
    blue: "bg-blue-400", purple: "bg-violet-400", violet: "bg-violet-400",
    emerald: "bg-emerald-400", amber: "bg-[#bb0051]", rose: "bg-rose-400", slate: "bg-slate-400",
  };
  const bgMap: Record<string, string> = {
    blue: "bg-slate-50/80 border-slate-100/80", purple: "bg-slate-50/80 border-slate-100/80",
    violet: "bg-slate-50/80 border-slate-100/80", emerald: "bg-slate-50/80 border-slate-100/80",
    amber: "bg-slate-50/80 border-slate-100/80", rose: "bg-slate-50/80 border-slate-100/80",
    slate: "bg-slate-50/80 border-slate-100/80",
  };
  const textMap: Record<string, string> = {
    blue: "text-blue-600", purple: "text-violet-600", violet: "text-violet-600",
    emerald: "text-emerald-600", amber: "text-[#bb0051]", rose: "text-rose-600", slate: "text-slate-500",
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 18 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{
        delay: index * 0.055,
        duration: 0.38,
        ease: [0.25, 0.46, 0.45, 0.94],
      }}
      whileHover={{ scale: 1.012, transition: { duration: 0.18 } }}
      className={`relative rounded-xl border cursor-pointer overflow-hidden transition-all duration-200 ${
        isSelected
          ? "bg-white border-slate-300 shadow-sm ring-[1.5px] ring-slate-300/70"
          : "bg-white/55 border-white/70 shadow-sm hover:shadow-md hover:bg-white/80"
      }`}
      style={{ backdropFilter: "blur(8px)" }}
      onClick={() => onToggleExpand(key)}
    >

      <div className="px-3 py-2.5">
        {/* Header row */}
        <div className="flex items-center gap-2.5">
          {/* Checkbox */}
          <motion.div
            whileTap={{ scale: 0.8 }}
            className="flex-shrink-0"
            onClick={(e) => {
              e.stopPropagation();
              onToggleSelect(key);
            }}
          >
            {isSelected ? (
              <motion.div
                initial={{ scale: 0.6 }}
                animate={{ scale: 1 }}
                className="w-[15px] h-[15px] rounded-[4px] bg-indigo-500 flex items-center justify-center shadow-sm shadow-indigo-100"
              >
                <svg
                  className="w-[9px] h-[9px] text-white"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  strokeWidth={3.5}
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M5 13l4 4L19 7"
                  />
                </svg>
              </motion.div>
            ) : (
              <div className="w-[15px] h-[15px] rounded-[4px] border-[1.5px] border-slate-300 hover:border-blue-400 transition-colors" />
            )}
          </motion.div>

          {/* Word text */}
          <span className="flex-1 font-semibold text-slate-800 text-[13px] leading-snug min-w-0 truncate">
            {displayWord}
          </span>

          {/* Chevron */}
          <motion.div
            animate={{ rotate: isExpanded ? 180 : 0 }}
            transition={{ duration: 0.22, ease: "easeInOut" }}
            className="flex-shrink-0 text-slate-400"
          >
            <ChevronDown size={14} />
          </motion.div>
        </div>

        {/* Collapsed translation preview */}
        {!isExpanded && (t?.translation || simpleTranslation) && (
          <p className="mt-1 ml-[27px] text-[11px] text-slate-500 truncate leading-relaxed">
            {t?.translation || simpleTranslation}
          </p>
        )}

        {/* Expanded details */}
        <AnimatePresence>
          {isExpanded && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: "auto", opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              transition={{ duration: 0.27, ease: [0.04, 0.62, 0.23, 0.98] }}
              style={{ overflow: "hidden" }}
            >
              <div className="mt-2.5 pt-2.5 border-t border-slate-100/80 space-y-1.5">
                {details.map((detail, i) => (
                  <motion.div
                    key={detail.label}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: i * 0.045, duration: 0.22 }}
                    className={`rounded-lg p-2 border text-[11px] ${bgMap[detail.color]}`}
                  >
                    {/* Label with colored bar */}
                    <div className="flex items-center gap-1.5 mb-1">
                      <div
                        className={`h-[3px] w-3 rounded-full ${barMap[detail.color]}`}
                      />
                      <span
                        className={`font-bold text-[9.5px] uppercase tracking-widest ${textMap[detail.color]}`}
                      >
                        {detail.label}
                      </span>
                    </div>
                    {/* Content */}
                    {detail.source !== undefined ? (
                      <div className="text-slate-600 leading-relaxed space-y-0.5">
                        <p className="italic">"{detail.source}"</p>
                        <p className="text-slate-500">→ "{detail.target}"</p>
                      </div>
                    ) : (
                      <p className="text-slate-600 leading-relaxed">
                        {detail.text}
                      </p>
                    )}
                  </motion.div>
                ))}

                {/* View source */}
                {word.url && (
                  <motion.button
                    initial={{ opacity: 0, y: 4 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: details.length * 0.045 + 0.05 }}
                    whileHover={{ scale: 1.03 }}
                    whileTap={{ scale: 0.96 }}
                    onClick={(e) => {
                      e.stopPropagation();
                      onOpenUrl(word.url!);
                    }}
                    className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-[11px] font-semibold text-white bg-gradient-to-r from-slate-600 to-slate-700 hover:from-slate-500 hover:to-slate-600 shadow-sm transition-all"
                  >
                    <ExternalLink size={11} />
                    View source
                  </motion.button>
                )}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </motion.div>
  );
}

// ──────────────────────────── Empty State ───────────────────────────────────

function EmptyState({ isSearch }: { isSearch: boolean }) {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.88 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.4, ease: [0.25, 0.46, 0.45, 0.94] }}
      className="flex flex-col items-center justify-center py-12 px-4 text-center"
    >
      <motion.div
        animate={{ y: [0, -9, 0] }}
        transition={{ duration: 2.8, repeat: Infinity, ease: "easeInOut" }}
        className="relative w-16 h-16 rounded-2xl bg-gradient-to-br from-blue-100/80 to-purple-100/80 flex items-center justify-center mb-4 shadow-sm"
        style={{ backdropFilter: "blur(8px)" }}
      >
        {isSearch ? (
          <Search className="text-blue-400" size={26} />
        ) : (
          <BookOpen className="text-purple-400" size={26} />
        )}
        <motion.div
          animate={{ scale: [1, 1.15, 1], opacity: [0.3, 0.6, 0.3] }}
          transition={{ duration: 2, repeat: Infinity }}
          className="absolute -top-1 -right-1 w-5 h-5 rounded-full bg-gradient-to-br from-blue-200 to-purple-200 flex items-center justify-center"
        >
          <Sparkles size={10} className="text-purple-500" />
        </motion.div>
      </motion.div>

      <h3 className="text-[13px] font-bold text-slate-700 mb-1.5">
        {isSearch ? "No matches found" : "No translations yet"}
      </h3>
      <p className="text-[11px] text-slate-400 max-w-[170px] leading-relaxed">
        {isSearch
          ? "Try a different search term"
          : "Highlight text on any webpage to start building your collection"}
      </p>

      {!isSearch && (
        <div className="flex gap-2 mt-5">
          {[0, 0.22, 0.44].map((delay, i) => (
            <motion.div
              key={i}
              animate={{ scale: [1, 1.5, 1], opacity: [0.35, 1, 0.35] }}
              transition={{
                duration: 1.3,
                repeat: Infinity,
                delay,
                ease: "easeInOut",
              }}
              className="w-1.5 h-1.5 rounded-full bg-gradient-to-r from-blue-400 to-purple-500"
            />
          ))}
        </div>
      )}
    </motion.div>
  );
}

// ──────────────────────────────── App ───────────────────────────────────────

export default function App() {
  const [words, setWords] = useState<Word[]>([]);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [search, setSearch] = useState("");
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [targetLang, setTargetLang] = useState("en");
  const [mode, setMode] = useState("smart");
  const [expandedWords, setExpandedWords] = useState<Set<string>>(new Set());
  const [ankiStatus, setAnkiStatus] = useState<{
    msg: string;
    error: boolean;
  } | null>(null);
  const [isExporting, setIsExporting] = useState(false);
  const ankiTimerRef = useRef<ReturnType<typeof setTimeout>>();

  useEffect(() => {
    chromeLoadWords().then(setWords);
    chromeLoadSettings().then((s) => {
      if (s?.targetLang) setTargetLang(s.targetLang);
      if (s?.mode) setMode(s.mode);
    });
  }, []);

  const handleLangChange = (lang: string) => {
    setTargetLang(lang);
    chromeSaveSettings({ targetLang: lang, mode });
  };
  const handleModeChange = (m: string) => {
    setMode(m);
    chromeSaveSettings({ targetLang, mode: m });
  };

  const filtered = useMemo(() => {
    const q = search.toLowerCase().trim();
    if (!q) return words;
    return words.filter((w) => {
      const display = (w.lemma || w.text).toLowerCase();
      if (display.includes(q)) return true;
      const t = w.translation;
      if (typeof t === "object" && t !== null) {
        return (
          (t.translation || "").toLowerCase().includes(q) ||
          (t.meaning || "").toLowerCase().includes(q)
        );
      }
      return String(t).toLowerCase().includes(q);
    });
  }, [words, search]);

  const allSelected =
    filtered.length > 0 &&
    filtered.every((w) => selected.has(w.lemma || w.text));

  const toggleSelect = useCallback((key: string) => {
    setSelected((prev) => {
      const next = new Set(prev);
      next.has(key) ? next.delete(key) : next.add(key);
      return next;
    });
  }, []);

  const toggleSelectAll = useCallback(() => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (allSelected) {
        filtered.forEach((w) => next.delete(w.lemma || w.text));
      } else {
        filtered.forEach((w) => next.add(w.lemma || w.text));
      }
      return next;
    });
  }, [allSelected, filtered]);

  const toggleExpand = useCallback((key: string) => {
    setExpandedWords((prev) => {
      const next = new Set(prev);
      next.has(key) ? next.delete(key) : next.add(key);
      return next;
    });
  }, []);

  const handleDelete = async () => {
    const lemmas = [...selected];
    await chromeDeleteWords(lemmas);
    setWords((prev) =>
      prev.filter((w) => !lemmas.includes(w.lemma || w.text))
    );
    setSelected(new Set());
  };

  const handleAnkiExport = async () => {
    setIsExporting(true);
    clearTimeout(ankiTimerRef.current);
    try {
      if (!isChromeExt) {
        await new Promise((r) => setTimeout(r, 900));
        setAnkiStatus({ msg: "✓ 4 added (demo mode)", error: false });
      } else {
        const res = await chrome.runtime.sendMessage({
          action: "exportToAnki",
        });
        if (res.error) {
          setAnkiStatus({
            msg: "Anki not running. Open Anki with AnkiConnect.",
            error: true,
          });
        } else if (res.empty) {
          setAnkiStatus({ msg: "No words to export.", error: false });
        } else {
          const parts: string[] = [];
          if (res.added) parts.push(`${res.added} added`);
          if (res.duplicates) parts.push(`${res.duplicates} already in Anki`);
          setAnkiStatus({ msg: `✓ ${parts.join(", ")}`, error: false });
        }
      }
    } catch {
      setAnkiStatus({
        msg: "Anki not running. Open Anki with AnkiConnect.",
        error: true,
      });
    } finally {
      setIsExporting(false);
      ankiTimerRef.current = setTimeout(() => setAnkiStatus(null), 4500);
    }
  };

  const handleOpenUrl = useCallback((url: string) => {
    if (isChromeExt) {
      chrome.tabs.create({ url });
    } else {
      window.open(url, "_blank");
    }
  }, []);

  return (
    <div
      className="relative w-[380px] flex flex-col overflow-hidden"
      style={{
        height: "560px",
        background:
          "linear-gradient(135deg, #f8fafc 0%, rgba(219,234,254,0.25) 50%, rgba(237,233,254,0.25) 100%)",
        fontFamily: "'Plus Jakarta Sans', ui-sans-serif, system-ui, sans-serif",
      }}
    >
      {/* Animated background orbs */}
      <BackgroundOrbs />

      {/* Main content */}
      <div className="relative z-10 flex flex-col h-full">
        {/* ── Header ──────────────────────────────────── */}
        <header
          className="flex items-center justify-between px-4 py-3 border-b border-white/60"
          style={{ backdropFilter: "blur(12px)", background: "rgba(255,255,255,0.45)" }}
        >
          <div className="flex items-center gap-2.5">
            {/* Logo orb */}
            <div className="relative flex-shrink-0">
              <motion.div
                whileHover={{ scale: 1.08 }}
                className="w-9 h-9 rounded-xl flex items-center justify-center shadow-lg"
                style={{
                  background: "linear-gradient(135deg, #4f46e5, #6366f1)",
                  boxShadow: "0 4px 12px rgba(99,102,241,0.25)",
                }}
              >
                <Languages className="text-white" size={18} />
              </motion.div>
              {/* Online dot */}
              <span className="absolute -top-0.5 -right-0.5 flex h-2.5 w-2.5">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
                <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-400 border-2 border-white" />
              </span>
            </div>

            <div>
              <h1 className="text-[15px] font-extrabold leading-none text-slate-800">
                Contxtly
              </h1>
              <p className="text-[10px] text-slate-400 leading-none mt-0.5 font-medium">
                Contextual translator
              </p>
            </div>
          </div>

          {/* Settings toggle */}
          <motion.button
            whileHover={{ scale: 1.07 }}
            whileTap={{ scale: 0.93 }}
            onClick={() => setSettingsOpen((v) => !v)}
            className="w-8 h-8 rounded-xl flex items-center justify-center transition-all duration-200"
            style={
              settingsOpen
                ? {
                    background: "#4f46e5",
                    color: "white",
                    boxShadow: "0 2px 8px rgba(79,70,229,0.2)",
                  }
                : {
                    background: "rgba(255,255,255,0.75)",
                    color: "#64748b",
                    border: "1px solid rgba(255,255,255,0.9)",
                  }
            }
          >
            <motion.div
              animate={{ rotate: settingsOpen ? 90 : 0 }}
              transition={{ duration: 0.28, ease: "easeInOut" }}
            >
              <Settings size={16} />
            </motion.div>
          </motion.button>
        </header>

        {/* ── Settings Panel ───────────────────────────── */}
        <AnimatePresence>
          {settingsOpen && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: "auto", opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              transition={{ duration: 0.3, ease: [0.04, 0.62, 0.23, 0.98] }}
              style={{ overflow: "hidden" }}
            >
              <div
                className="px-4 py-3 border-b border-white/60 space-y-3"
                style={{
                  backdropFilter: "blur(12px)",
                  background: "rgba(248,250,252,0.7)",
                }}
              >
                {/* Translate to */}
                <div>
                  <div className="flex items-center gap-1.5 mb-1.5">
                    <div className="h-[3px] w-3.5 rounded-full bg-slate-400" />
                    <label className="text-[9.5px] font-bold uppercase tracking-widest text-slate-500">
                      Translate to
                    </label>
                  </div>
                  <select
                    value={targetLang}
                    onChange={(e) => handleLangChange(e.target.value)}
                    className="w-full px-3 py-2 text-[12px] rounded-xl border border-blue-100 text-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-200 transition-all cursor-pointer font-medium"
                    style={{ background: "rgba(239,246,255,0.7)" }}
                  >
                    {LANGUAGES.map((l) => (
                      <option key={l.code} value={l.code}>
                        {l.label}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Translation mode */}
                <div>
                  <div className="flex items-center gap-1.5 mb-1.5">
                    <div className="h-[3px] w-3.5 rounded-full bg-slate-400" />
                    <label className="text-[9.5px] font-bold uppercase tracking-widest text-slate-500">
                      Translation mode
                    </label>
                  </div>
                  <select
                    value={mode}
                    onChange={(e) => handleModeChange(e.target.value)}
                    className="w-full px-3 py-2 text-[12px] rounded-xl border border-purple-100 text-slate-700 focus:outline-none focus:ring-2 focus:ring-purple-200 transition-all cursor-pointer font-medium"
                    style={{ background: "rgba(245,243,255,0.7)" }}
                  >
                    <option value="simple">Simple</option>
                    <option value="smart">✨ Smart (with context)</option>
                  </select>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* ── Toolbar ──────────────────────────────────── */}
        <div
          className="flex items-center gap-1.5 px-3 py-2 border-b border-slate-100/80"
          style={{ backdropFilter: "blur(12px)", background: "rgba(255,255,255,0.45)" }}
        >
          {/* Search */}
          <div className="flex-1 relative">
            <Search
              className="absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none"
              size={12}
            />
            <input
              type="text"
              placeholder="Search words..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-7 pr-6 py-1.5 text-[12px] rounded-lg border border-slate-200 bg-white text-slate-700 placeholder-slate-400 focus:outline-none focus:border-slate-400 focus:ring-1 focus:ring-slate-200 transition-all font-medium"
            />
            <AnimatePresence>
              {search && (
                <motion.button
                  initial={{ opacity: 0, scale: 0.6 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.6 }}
                  transition={{ duration: 0.15 }}
                  onClick={() => setSearch("")}
                  className="absolute right-2 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 transition-colors"
                >
                  <X size={12} />
                </motion.button>
              )}
            </AnimatePresence>
          </div>

          {/* Anki export */}
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={handleAnkiExport}
            disabled={isExporting}
            title="Export to Anki"
            className="w-8 h-8 rounded-lg flex items-center justify-center border border-slate-200 bg-white text-emerald-600 hover:bg-emerald-50 hover:border-emerald-200 hover:text-emerald-700 transition-all disabled:opacity-40 disabled:cursor-not-allowed"
          >
            <motion.div
              animate={isExporting ? { rotate: 360 } : {}}
              transition={isExporting ? { duration: 0.9, repeat: Infinity, ease: "linear" } : {}}
            >
              <Layers size={14} />
            </motion.div>
          </motion.button>

          {/* Select all */}
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={toggleSelectAll}
            title={allSelected ? "Deselect all" : "Select all"}
            className={`w-8 h-8 rounded-lg flex items-center justify-center border transition-all ${
              allSelected
                ? "bg-indigo-50 border-indigo-200 text-indigo-600"
                : "bg-white border-slate-200 text-slate-500 hover:bg-slate-50 hover:text-slate-700"
            }`}
          >
            {allSelected ? <CheckSquare size={14} /> : <Square size={14} />}
          </motion.button>

          {/* Delete */}
          <AnimatePresence>
            {selected.size > 0 && (
              <motion.button
                initial={{ opacity: 0, scale: 0.7, width: 0 }}
                animate={{ opacity: 1, scale: 1, width: 32 }}
                exit={{ opacity: 0, scale: 0.7, width: 0 }}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={handleDelete}
                title={`Delete ${selected.size} selected`}
                className="relative h-8 rounded-lg flex items-center justify-center border border-slate-200 bg-white text-red-400 hover:bg-red-50 hover:border-red-200 hover:text-red-500 transition-all overflow-visible flex-shrink-0"
              >
                <Trash2 size={13} />
                <motion.span
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  className="absolute -top-1.5 -right-1.5 w-[15px] h-[15px] rounded-full bg-red-400 text-white text-[9px] font-bold flex items-center justify-center border border-white"
                >
                  {selected.size}
                </motion.span>
              </motion.button>
            )}
          </AnimatePresence>
        </div>

        {/* ── Words List ───────────────────────────────── */}
        <div className="flex-1 overflow-y-auto px-3 py-2.5 space-y-1.5 custom-scroll">
          {filtered.length === 0 ? (
            <EmptyState isSearch={!!search} />
          ) : (
            filtered.map((word, index) => (
              <WordCard
                key={word.lemma || word.text}
                word={word}
                index={index}
                isSelected={selected.has(word.lemma || word.text)}
                isExpanded={expandedWords.has(word.lemma || word.text)}
                onToggleSelect={toggleSelect}
                onToggleExpand={toggleExpand}
                onOpenUrl={handleOpenUrl}
              />
            ))
          )}
        </div>

        {/* ── Footer ───────────────────────────────────── */}
        <footer
          className="flex items-center justify-between px-4 py-2.5 border-t border-white/60"
          style={{
            backdropFilter: "blur(12px)",
            background: "rgba(255,255,255,0.4)",
          }}
        >
          <div className="flex items-center gap-1.5">
            <div className="w-1.5 h-1.5 rounded-full bg-slate-300" />
            <span className="text-[11px] text-slate-500 font-semibold">
              {filtered.length} word{filtered.length !== 1 ? "s" : ""}
            </span>
          </div>

          <AnimatePresence mode="wait">
            {ankiStatus && (
              <motion.span
                key={ankiStatus.msg}
                initial={{ opacity: 0, y: 5 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -5 }}
                transition={{ duration: 0.2 }}
                className="text-[11px] font-semibold"
                style={{
                  color: ankiStatus.error ? "#ef4444" : "#059669",
                }}
              >
                {ankiStatus.msg}
              </motion.span>
            )}
          </AnimatePresence>
        </footer>
      </div>
    </div>
  );
}
