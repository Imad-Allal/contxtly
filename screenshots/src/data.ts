import type { WordTypeColorKey } from "./theme";

export interface MockWord {
  text: string;
  type: WordTypeColorKey;
  translation: string;
  meaning: string;
  context: string;
  savedAgo: string;
}

export const MOCK_WORDS: MockWord[] = [
  { text: "eine Rolle spielen", type: "collocation", translation: "to play a role", meaning: "A fixed German expression; the two words are often split by other words in the sentence.", context: "Anthropic, Microsoft und Google spielen beim KI-Rennen eine entscheidende Rolle.", savedAgo: "2m ago" },
  { text: "Abhängigkeit", type: "noun", translation: "dependency", meaning: "A state of relying on someone or something.", context: "Das schafft gefährliche Abhängigkeiten für die Weltwirtschaft.", savedAgo: "5m ago" },
  { text: "vorschlagen", type: "verb", translation: "to propose", meaning: "To suggest an idea or plan for consideration.", context: "Er wollte einen neuen Plan vorschlagen.", savedAgo: "12m ago" },
  { text: "Technologiekonzerne", type: "compound", translation: "tech corporations", meaning: "Large technology companies operating at scale.", context: "Die großen Technologiekonzerne haben ein beispielloses Tempo vorgelegt.", savedAgo: "1h ago" },
  { text: "über den Tellerrand schauen", type: "expression", translation: "to think outside the box", meaning: "To look beyond one's immediate perspective.", context: "Gute Forscher müssen über den Tellerrand schauen.", savedAgo: "3h ago" },
  { text: "einzelne", type: "adjective", translation: "individual / single", meaning: "Referring to one or a few items rather than the whole.", context: "Es gehe nicht mehr nur um einzelne Produkte, sondern um ganze Ökosysteme.", savedAgo: "yesterday" },
  { text: "nachhaltig", type: "adjective", translation: "sustainable", meaning: "Able to be maintained at a certain rate or level.", context: "Eine nachhaltige Lösung für das Klimaproblem.", savedAgo: "yesterday" },
  { text: "Weltwirtschaft", type: "noun", translation: "global economy", meaning: "The economic system of the whole world.", context: "Die Weltwirtschaft zeigt Zeichen der Erholung.", savedAgo: "2d ago" },
  { text: "beschleunigen", type: "verb", translation: "to accelerate", meaning: "To increase the speed of something.", context: "Neue Technologien beschleunigen den Wandel.", savedAgo: "2d ago" },
  { text: "Wettbewerbsvorteil", type: "compound", translation: "competitive advantage", meaning: "A condition that puts a company in a favorable position.", context: "Der Wettbewerbsvorteil durch KI ist enorm.", savedAgo: "3d ago" },
  { text: "in Frage kommen", type: "expression", translation: "to be a possibility", meaning: "To be considered as an option.", context: "Für diesen Job kommt er nicht in Frage.", savedAgo: "3d ago" },
  { text: "investieren", type: "verb", translation: "to invest", meaning: "To put money into something with the hope of profit.", context: "Große Konzerne investieren Milliarden in KI.", savedAgo: "4d ago" },
];

export const ARTICLE = {
  source: "Der Spiegel",
  date: "22. April 2026",
  headline: "Wie der KI-Wettlauf die Weltwirtschaft verändert",
  subhead: "Anthropic, Microsoft und Google investieren Milliarden — und schaffen neue Abhängigkeiten, die das globale Gleichgewicht verschieben.",
  paragraphs: [
    "Die großen $TECHNOLOGIEKONZERNE$ haben in den letzten Monaten ein beispielloses Tempo vorgelegt. Anthropic, Microsoft und Google $SPIELEN$ beim KI-Rennen eine entscheidende $ROLLE$ und treiben die globale Entwicklung weiter an. Das schafft gefährliche $ABHÄNGIGKEITEN$ und Risiken für die $WELTWIRTSCHAFT$.",
    "Analysten sehen in dieser Entwicklung einen entscheidenden Moment. „Wir beobachten, wie sich ein neues Gleichgewicht zwischen öffentlichen und privaten Akteuren bildet“, sagt die Ökonomin Clara Reinhardt. Es gehe längst nicht mehr nur um $EINZELNE$ Produkte, sondern um die Kontrolle über ganze Ökosysteme.",
    "Gleichzeitig wächst der politische Druck. Regulierungsbehörden in Brüssel und Washington fordern mehr Transparenz, während Unternehmen versuchen, schneller zu liefern als die Konkurrenz.",
  ],
};
