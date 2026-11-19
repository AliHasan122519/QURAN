export type Kind = 'quran' | 'hadith' | 'poem' | 'generic';
export type SourceId = string;                              // a tab id from the content manifest («quran», «jami», …); new ones can be added by a content update
export type MatchType = 'literal' | 'normalized' | 'textual' | 'derived' | 'semantic';
export interface Tab { id: SourceId; label: string; kind: Kind; file: string | null; sha256: string | null; count?: number; placeholder?: string; hint?: string; card?: 'meaning'; }
export interface Manifest { schema: number; version: number; updated?: string; apk?: { versionCode: number; url: string; notes?: string }; tabs: Tab[]; }
export interface Doc {
  id: string; src: SourceId; text: string;
  surah?: number; surahName?: string; ayah?: number;                              // Qur'an
  page?: number; number?: number; takhrij?: string; grade?: string; tier?: 'v' | 'h' | 'm' | 'l';        // hadith
  chapter?: string; verse?: number; shatr1?: string; shatr2?: string;             // poem (verse number, chapter title, the two hemistichs)
  ref?: string; explanation?: string; source?: string;                                              // generic entries
}
export interface Hit { id: string; src: SourceId; ord: number; score: number; type: MatchType; via?: string; }
export interface SearchResult {
  query: string; hits: Hit[]; terms: string[]; root: string; related: string[]; highlight: Set<string>; ms: number;
}
export interface Lookup {
  query: string; directCount: number; semanticCount: number; expansion: { root: string; terms: string[] } | null; section?: string;
  results: { hit: Hit; doc: Doc; matchType: 'نصي' | 'دلالي'; matchedTerm: string }[]; highlight: Set<string>; capped: boolean;
}
