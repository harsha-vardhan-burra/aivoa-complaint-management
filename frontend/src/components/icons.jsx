// Small set of inline line-style icons shared across the UI. Kept as plain
// SVG (no icon package dependency) so every glyph inherits currentColor and
// stays crisp at any size.

export const CalendarIcon = (props) => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" {...props}>
    <rect x="3.5" y="5" width="17" height="16" rx="2" />
    <path d="M8 3v4M16 3v4M3.5 10h17" />
  </svg>
);

export const TrayUploadIcon = (props) => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" {...props}>
    <path d="M12 3v11M8 10l4-4 4 4" />
    <path d="M4 15v3.5A2.5 2.5 0 0 0 6.5 21h11A2.5 2.5 0 0 0 20 18.5V15" />
  </svg>
);

export const DocumentIcon = (props) => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" {...props}>
    <path d="M7 3h7l4 4v13a1 1 0 0 1-1 1H7a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1Z" />
    <path d="M14 3v4h4M9 12h6M9 15.5h6" />
  </svg>
);

export const SendIcon = (props) => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" {...props}>
    <path d="M4 12l16-7-6.5 16-2.7-6.8L4 12Z" />
  </svg>
);

export const CloseIcon = (props) => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" {...props}>
    <path d="M5 5l14 14M19 5 5 19" />
  </svg>
);

export const AssistantMarkIcon = (props) => (
  <svg viewBox="0 0 24 24" fill="none" {...props}>
    <circle cx="8.5" cy="9" r="4" fill="currentColor" opacity="0.9" />
    <circle cx="15.5" cy="15" r="4" fill="currentColor" opacity="0.45" />
  </svg>
);

export const ResetIcon = (props) => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" {...props}>
    <path d="M4 4v6h6" />
    <path d="M4.5 13a8 8 0 1 0 2.4-6.9L4 9" />
  </svg>
);
