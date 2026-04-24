import { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Layers, ChevronDown, FileDown, FileText, FileCode2, Rows3 } from "lucide-react";
import type { Word, TranslationData } from "../types";
import { MOTION, RADIUS } from "../theme";

type Format = "anki" | "csv" | "json" | "quizlet";

interface Props {
  words: Word[];
  selectedWords: Word[];
  isExporting: boolean;
  onAnki: (words: Word[]) => void;
}

function translationText(w: Word): string {
  if (typeof w.translation === "string") return w.translation;
  const t = w.translation as TranslationData;
  return t.translation || t.meaning || "";
}

function download(filename: string, content: string, mime: string) {
  const blob = new Blob([content], { type: mime });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

function toCSV(words: Word[]): string {
  const esc = (s: string) => `"${String(s).replace(/"/g, '""')}"`;
  const header = ["word", "lemma", "translation", "meaning", "context", "url"].join(",");
  const rows = words.map((w) => {
    const t = typeof w.translation === "object" ? (w.translation as TranslationData) : null;
    return [
      esc(w.text),
      esc(w.lemma ?? ""),
      esc(t?.translation ?? (typeof w.translation === "string" ? w.translation : "")),
      esc(t?.meaning ?? ""),
      esc(w.context ?? ""),
      esc(w.url ?? ""),
    ].join(",");
  });
  return [header, ...rows].join("\n");
}

function toQuizlet(words: Word[]): string {
  return words.map((w) => `${w.text}\t${translationText(w)}`).join("\n");
}

export function ExportMenu({ words, selectedWords, isExporting, onAnki }: Props) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  const target = selectedWords.length > 0 ? selectedWords : words;
  const isEmpty = target.length === 0;
  const disabled = isExporting || isEmpty;

  useEffect(() => {
    function onDoc(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    }
    if (open) document.addEventListener("mousedown", onDoc);
    return () => document.removeEventListener("mousedown", onDoc);
  }, [open]);

  useEffect(() => {
    if (isEmpty && open) setOpen(false);
  }, [isEmpty, open]);

  function run(fmt: Format) {
    setOpen(false);
    if (fmt === "anki") return onAnki(target);
    const date = new Date().toISOString().slice(0, 10);
    if (fmt === "csv") download(`contxtly-${date}.csv`, toCSV(target), "text/csv");
    else if (fmt === "json") download(`contxtly-${date}.json`, JSON.stringify(target, null, 2), "application/json");
    else if (fmt === "quizlet") download(`contxtly-${date}.txt`, toQuizlet(target), "text/plain");
  }

  const OPTIONS: { fmt: Format; label: string; desc: string; icon: typeof FileDown }[] = [
    { fmt: "anki",    label: "Anki",    desc: "Send to Anki (.apkg via AnkiConnect)", icon: Layers },
    { fmt: "csv",     label: "CSV",     desc: "Spreadsheet-friendly",                 icon: Rows3 },
    { fmt: "json",    label: "JSON",    desc: "Full data, developer-friendly",        icon: FileCode2 },
    { fmt: "quizlet", label: "Quizlet", desc: "Tab-separated term/definition",        icon: FileText },
  ];

  return (
    <div ref={ref} className="relative">
      <motion.button
        whileHover={disabled ? undefined : { scale: 1.06 }}
        whileTap={disabled ? undefined : { scale: 0.94 }}
        onClick={() => { if (!disabled) setOpen((v) => !v); }}
        disabled={disabled}
        aria-label={isEmpty ? "Export (no words to export)" : "Export"}
        aria-haspopup="menu"
        aria-expanded={open}
        title={isEmpty ? "Save some words to export" : "Export"}
        className="h-8 px-1.5 rounded-xl flex items-center gap-0.5 border border-slate-200 bg-white text-emerald-600 hover:bg-emerald-50 hover:border-emerald-200 hover:text-emerald-700 transition-all disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:bg-white disabled:hover:border-slate-200 disabled:hover:text-emerald-600"
      >
        <motion.div
          animate={isExporting ? { rotate: 360 } : {}}
          transition={isExporting ? { duration: 0.9, repeat: Infinity, ease: "linear" } : {}}
        >
          <Layers size={14} />
        </motion.div>
        <ChevronDown size={10} style={{ opacity: 0.6 }} />
      </motion.button>

      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, y: -4, scale: 0.96 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -4, scale: 0.96 }}
            transition={MOTION.fast}
            role="menu"
            className="absolute right-0 top-full mt-1 z-30 bg-white overflow-hidden"
            style={{
              borderRadius: RADIUS.md,
              minWidth: 220,
              border: "1px solid #e2e8f0",
              boxShadow: "0 12px 32px rgba(15,23,42,0.15)",
            }}
          >
            {OPTIONS.map((o) => {
              const Icon = o.icon;
              return (
                <button
                  key={o.fmt}
                  role="menuitem"
                  onClick={() => run(o.fmt)}
                  className="w-full flex items-start gap-2.5 px-3 py-2 text-left hover:bg-slate-50 transition-colors"
                >
                  <div className="flex-shrink-0 w-7 h-7 rounded-lg bg-slate-50 flex items-center justify-center text-slate-600">
                    <Icon size={14} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-[12px] font-bold text-slate-800">{o.label}</p>
                    <p className="text-[10.5px] text-slate-500 leading-snug">{o.desc}</p>
                  </div>
                </button>
              );
            })}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
