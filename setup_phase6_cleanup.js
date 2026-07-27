/**
 * setup_phase6_cleanup.js
 *
 * Phase 6 Cleanup -- Remove tutorial/demo state contamination from Redux.
 * Must be applied and verified before Phase 7.
 *
 * Root cause: complaintSlice.js and copilotSlice.js shipped with a
 * hardcoded "Apollo Pharmacy" complaint/risk/conversation fixture baked
 * directly into their initialState. This meant every fresh page load
 * (and every "Reset Form" click, since resetComplaint returned that same
 * initialState) already showed a fully-populated complaint and a
 * pre-executed AI conversation that never actually went through
 * PromptInput -> processComplaintMessage -> LangGraph -> Groq.
 *
 * Fix, frontend-only, no backend/API/schema changes:
 *   1. complaintSlice.js -- initialState.complaint is now genuinely
 *      empty (all 13 ComplaintBase fields null), initialState.riskAssessment
 *      is genuinely unassessed (severity/rationale/confidence/
 *      recommended_action null, missing_fields []), missingFields is [].
 *      triageStatus stays "Pending Triage". resetComplaint is unchanged
 *      (it already returns initialState) -- it now correctly restores an
 *      empty state instead of the old Apollo fixture.
 *   2. copilotSlice.js -- initial conversation keeps only the real
 *      greeting message. The fake pre-baked Apollo user message and
 *      assistant reply are removed. A new draftText field (plus a
 *      setDraftText action) is added alongside the slice's existing
 *      loading/error/uploadedDocument UI state so the compose-box text
 *      can be set from outside PromptInput (needed for the example
 *      chip below) without introducing a new hook or lifting state into
 *      a separate module.
 *   3. PromptInput.jsx -- textarea value now reads/writes
 *      state.copilot.draftText via Redux instead of local useState.
 *      handleSend's logic (call processComplaintMessage, dispatch
 *      setComplaint/setRiskAssessment/setMissingFields, error handling)
 *      is completely unchanged -- this is a state-source swap, not a
 *      pipeline change.
 *   4. CopilotPanel.jsx -- adds a clearly labelled "Try an example"
 *      chip. Clicking it only dispatches setDraftText(EXAMPLE_TEXT); it
 *      does not call the API, does not dispatch setComplaint/
 *      setRiskAssessment, and contains no canned response. The user
 *      still sends it through the same PromptInput -> Send button (or
 *      Enter) flow as anything they type themselves.
 *   5. RiskAssessment.jsx -- minimal presentation fix so a null
 *      severity (the new unassessed initial/reset state) renders as
 *      "Not Yet Assessed" with an empty gauge, instead of the old
 *      indexOf(null) === -1 -> Math.max(0, -1) === 0 bug that
 *      incorrectly filled the first ("low") gauge segment and implied
 *      an assessment had already happened.
 * Patches:
 *   frontend/src/App.css (adds .risk-badge.risk-unassessed and
 *   .example-chip* rules, reusing existing design tokens -- no new
 *   colors introduced)
 *
 * Explicitly NOT touched: backend/, GroqService, LangGraph, Pydantic
 * schemas, API contracts, processComplaintMessage, ComplaintForm.jsx,
 * TriageStatus.jsx, api.js.
 *
 * Run from the project root (the folder containing backend/ and
 * frontend/):
 *   node setup_phase6_cleanup.js
 */

const fs = require('fs');
const path = require('path');

function writeFile(relativePath, content) {
  const fullPath = path.join(__dirname, relativePath);
  fs.mkdirSync(path.dirname(fullPath), { recursive: true });
  fs.writeFileSync(fullPath, content, 'utf8');
  console.log(`Wrote ${relativePath}`);
}

function patchFile(relativePath, replacements) {
  const fullPath = path.join(__dirname, relativePath);
  let content = fs.readFileSync(fullPath, 'utf8');
  for (const { anchor, from, to } of replacements) {
    if (!content.includes(from)) {
      throw new Error(
        `Could not find expected anchor "${anchor}" in ${relativePath}. ` +
        `The file may have changed since this script was written -- ` +
        `please check it manually.`
      );
    }
    content = content.replace(from, to);
  }
  fs.writeFileSync(fullPath, content, 'utf8');
  console.log(`Patched ${relativePath}`);
}

// =============================================================================
// FRONTEND: complaint slice -- genuinely empty initial/reset state
// =============================================================================

writeFile('frontend/src/features/complaint/complaintSlice.js', `
import { createSlice } from '@reduxjs/toolkit';

// Field names here match the backend's ComplaintBase / RiskAssessmentBase
// schemas (see backend/app/schemas) so that API responses can be stored
// directly without a translation layer. The non-destructive merge of a
// conversational edit into the existing complaint already happens
// server-side (LangGraph's merge_patch node, Phase 5) -- this slice just
// mirrors whatever the backend returns as the single source of truth.
//
// initialState is genuinely empty: no complaint has been submitted yet,
// so every field is null and no risk assessment has run. (A prior
// version of this file hardcoded a fictional "Apollo Pharmacy" complaint
// and risk assessment here as a tutorial fixture -- that leaked into
// real application state on every fresh load and every Reset Form click.
// The same example is now offered as an optional "Try an example" chip
// in CopilotPanel, which only inserts input text and runs it through the
// real pipeline -- it never writes directly to this state.)
const initialState = {
  triageStatus: "Pending Triage",
  complaint: {
    complaint_source: null,
    customer_name: null,
    product_name: null,
    product_strength_grade: null,
    batch_number: null,
    manufacturing_date: null,
    expiry_date: null,
    quantity_affected: null,
    complaint_type: null,
    complaint_date: null,
    detailed_complaint_description: null,
    initial_severity: null,
    priority: null,
  },
  riskAssessment: {
    severity: null,
    rationale: null,
    missing_fields: [],
    confidence: null,
    recommended_action: null,
  },
  missingFields: [],
};

const complaintSlice = createSlice({
  name: 'complaint',
  initialState,
  reducers: {
    // Full replace: used whenever we receive a fresh merged_complaint
    // from POST /api/ai/complaints/process. The backend already
    // performed the non-destructive merge, so the frontend does not
    // do its own patching here.
    setComplaint: (state, action) => {
      state.complaint = action.payload;
    },
    setRiskAssessment: (state, action) => {
      state.riskAssessment = action.payload;
    },
    // missing_fields comes from the AI's own risk assessment
    // (PROJECT_CONTEXT.md Data Integrity Rule 6: missing information
    // must be explicit) rather than a client-side heuristic.
    setMissingFields: (state, action) => {
      state.missingFields = action.payload;
      state.triageStatus = action.payload.length === 0 ? "Ready to Commit" : "Pending Triage";
    },
    // Returns the (now genuinely empty) initialState -- no demo data is
    // restored.
    resetComplaint: () => initialState,
  }
});

export const { setComplaint, setRiskAssessment, setMissingFields, resetComplaint } = complaintSlice.actions;
export default complaintSlice.reducer;
`);

// =============================================================================
// FRONTEND: copilot slice -- real greeting only, plus draftText for the
// PromptInput compose box (so the example chip can populate it)
// =============================================================================

writeFile('frontend/src/features/copilot/copilotSlice.js', `
import { createSlice } from '@reduxjs/toolkit';

// Only the genuine assistant greeting ships in initial state. (A prior
// version of this file also hardcoded a fake user message and a fake
// assistant reply here, pre-simulating a conversation that never
// actually went through the API. Removed -- see CopilotPanel's "Try an
// example" chip for how that example complaint is now offered instead,
// as text the user can send through the real pipeline.)
const initialState = {
  messages: [
    {
      id: 1,
      role: 'assistant',
      content: "Hello! I am the AIVOA Copilot. Please describe the customer complaint or upload a document, and I will extract the details and assess the risk."
    }
  ],
  loading: false,
  error: null,
  uploadedDocument: null,
  // Backs the PromptInput textarea. Lives here (alongside the slice's
  // other compose-related UI state) rather than as PromptInput-local
  // useState so the example chip in CopilotPanel can populate it without
  // prop drilling or a new shared hook.
  draftText: ''
};

const copilotSlice = createSlice({
  name: 'copilot',
  initialState,
  reducers: {
    addMessage: (state, action) => { state.messages.push(action.payload); },
    setLoading: (state, action) => { state.loading = action.payload; },
    setError: (state, action) => { state.error = action.payload; },
    setUploadedDocument: (state, action) => { state.uploadedDocument = action.payload; },
    clearUploadedDocument: (state) => { state.uploadedDocument = null; },
    setDraftText: (state, action) => { state.draftText = action.payload; }
  }
});

export const {
  addMessage,
  setLoading,
  setError,
  setUploadedDocument,
  clearUploadedDocument,
  setDraftText
} = copilotSlice.actions;
export default copilotSlice.reducer;
`);

// =============================================================================
// FRONTEND: PromptInput -- same send pipeline, text now sourced from Redux
// so the example chip can populate it
// =============================================================================

writeFile('frontend/src/features/copilot/PromptInput.jsx', `
import { useDispatch, useSelector } from 'react-redux';
import { addMessage, setLoading, setError, setDraftText } from './copilotSlice';
import { setComplaint, setRiskAssessment, setMissingFields } from '../complaint/complaintSlice';
import { processComplaintMessage } from '../../services/api';
import { SendIcon } from '../../components/icons';

// Compose-box text lives in Redux (copilotSlice.draftText) rather than
// local useState so it can be set from outside this component -- e.g.
// CopilotPanel's "Try an example" chip -- without duplicating the send
// pipeline below. Everything from handleSend down is unchanged from the
// prior local-state version: same API call, same dispatches, same error
// handling.
const PromptInput = () => {
  const dispatch = useDispatch();
  const text = useSelector((state) => state.copilot.draftText);
  const currentComplaint = useSelector((state) => state.complaint.complaint);
  const loading = useSelector((state) => state.copilot.loading);

  const handleSend = async () => {
    const trimmed = text.trim();
    if (!trimmed || loading) return;

    dispatch(addMessage({ id: Date.now(), role: 'user', content: trimmed }));
    dispatch(setDraftText(''));
    dispatch(setLoading(true));
    dispatch(setError(null));

    try {
      const result = await processComplaintMessage(trimmed, currentComplaint);
      dispatch(setComplaint(result.complaint));
      dispatch(setRiskAssessment(result.risk));
      dispatch(setMissingFields(result.missing_fields));

      const summary = result.missing_fields.length > 0
        ? \`I've updated the complaint record. Still missing: \${result.missing_fields.join(', ')}.\`
        : "I've updated the complaint record. All key fields are now captured.";
      dispatch(addMessage({ id: Date.now() + 1, role: 'assistant', content: summary }));
    } catch (err) {
      // AI/network failure: report it and leave the existing complaint
      // state untouched rather than clearing or guessing at fields.
      const message = err?.response?.data?.detail || 'Something went wrong processing that message. Please try again.';
      dispatch(setError(message));
      dispatch(addMessage({ id: Date.now() + 1, role: 'assistant', content: message }));
    } finally {
      dispatch(setLoading(false));
    }
  };

  const handleKeyDown = (event) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="prompt-input-area">
      <textarea
        rows="2"
        placeholder="Ask about this complaint, or paste details to extract..."
        value={text}
        onChange={(event) => dispatch(setDraftText(event.target.value))}
        onKeyDown={handleKeyDown}
        disabled={loading}
      />
      <button type="button" onClick={handleSend} disabled={!text.trim() || loading} aria-label="Send message">
        <SendIcon className="send-icon" />
      </button>
    </div>
  );
};

export default PromptInput;
`);

// =============================================================================
// FRONTEND: CopilotPanel -- add the "Try an example" chip
// =============================================================================

writeFile('frontend/src/features/copilot/CopilotPanel.jsx', `
import { useRef } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import ChatMessage from './ChatMessage';
import PromptInput from './PromptInput';
import { setUploadedDocument, clearUploadedDocument, setDraftText } from './copilotSlice';
import { TrayUploadIcon, DocumentIcon, CloseIcon, AssistantMarkIcon, SparkleIcon } from '../../components/icons';
import './CopilotPanel.css';

// Plain input text for the real pipeline -- clicking the chip below only
// ever calls setDraftText(EXAMPLE_TEXT). It never dispatches setComplaint
// or setRiskAssessment directly, never calls the API itself, and carries
// no canned response. The user still submits it through the same
// PromptInput Send button (or Enter) as anything they type themselves,
// so it goes through the real processComplaintMessage -> LangGraph ->
// Groq -> Redux pipeline.
const EXAMPLE_TEXT = "Apollo Pharmacy reported discolored capsules in Amoxicillin Capsules 500 mg.";

const CopilotPanel = () => {
  const messages = useSelector((state) => state.copilot.messages);
  const uploadedDocument = useSelector((state) => state.copilot.uploadedDocument);
  const dispatch = useDispatch();
  const fileInputRef = useRef(null);

  const handleBrowseClick = () => {
    fileInputRef.current?.click();
  };

  const handleZoneKeyDown = (event) => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      handleBrowseClick();
    }
  };

  const handleFileChange = (event) => {
    const file = event.target.files && event.target.files[0];
    if (!file) return;
    // Local-only for now: records the selected file so the UI reflects
    // it honestly. Actual upload + extraction is Phase 8 (PDF pipeline).
    dispatch(setUploadedDocument({ name: file.name, size: file.size }));
    event.target.value = '';
  };

  const handleRemoveDocument = () => {
    dispatch(clearUploadedDocument());
  };

  const handleUseExample = () => {
    dispatch(setDraftText(EXAMPLE_TEXT));
  };

  return (
    <div className="copilot-container">
      <div className="copilot-header">
        <AssistantMarkIcon className="copilot-mark" />
        <h2>Complaint Intake Assistant</h2>
        <span className="preview-tag">Preview</span>
      </div>

      {/* Scrollable Content Area */}
      <div className="chat-history">
        <div
          className="upload-zone"
          role="button"
          tabIndex={0}
          onClick={handleBrowseClick}
          onKeyDown={handleZoneKeyDown}
          aria-label="Upload complaint document"
        >
          <TrayUploadIcon className="upload-icon" aria-hidden="true" />
          <p className="upload-title">Drag &amp; drop complaint document here</p>
          <p className="upload-subtitle">or <span className="upload-link">click to browse</span></p>
          <div className="upload-divider">
            <span>OR</span>
          </div>
          <button
            type="button"
            className="btn-paste"
            onClick={(event) => event.stopPropagation()}
          >
            <DocumentIcon className="btn-icon" />
            Paste Complaint Text / Email
          </button>
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,.docx,.txt,.eml"
            className="visually-hidden"
            onChange={handleFileChange}
            aria-hidden="true"
            tabIndex={-1}
          />
        </div>

        <div className="info-box">
          <strong>Supported formats:</strong> PDF, DOCX, TXT, EML &middot; Max file size 10MB
        </div>

        {uploadedDocument && (
          <div className="document-chip">
            <span className="document-chip-name">
              <DocumentIcon className="document-chip-icon" />
              {uploadedDocument.name}
            </span>
            <button
              type="button"
              className="document-chip-remove"
              onClick={handleRemoveDocument}
              aria-label={\`Remove \${uploadedDocument.name}\`}
            >
              <CloseIcon className="chip-remove-icon" />
            </button>
          </div>
        )}

        <div className="ai-assistant-box">
          <AssistantMarkIcon className="ai-icon" />
          <p className="ai-assistant-text">
            Upload a complaint document or paste text above. I will automatically extract the details and populate the form for you.
          </p>
        </div>

        <button
          type="button"
          className="example-chip"
          onClick={handleUseExample}
          aria-label="Try an example complaint"
        >
          <span className="example-chip-label">
            <SparkleIcon className="example-chip-icon" aria-hidden="true" />
            Try an example
          </span>
          <span className="example-chip-text">&ldquo;{EXAMPLE_TEXT}&rdquo;</span>
        </button>

        {/* Actual Chat Messages */}
        {messages.map((msg) => (
          <ChatMessage key={msg.id} role={msg.role} content={msg.content} />
        ))}
      </div>

      {/* Fixed Bottom Input */}
      <div className="copilot-actions">
        <PromptInput />
        <div className="disclaimer">AI responses may contain errors. Please verify information.</div>
      </div>
    </div>
  );
};

export default CopilotPanel;
`);

// =============================================================================
// FRONTEND: RiskAssessment -- minimal fix so an unassessed (null severity)
// state renders honestly instead of implying a "Low" assessment already ran
// =============================================================================

writeFile('frontend/src/features/complaint/RiskAssessment.jsx', `
import { useSelector } from 'react-redux';

// Matches the backend's severity enum (low/medium/high/critical) so the
// gauge always reflects a real value the AI can return, rather than a
// different label set the API would have to be mapped into.
const LEVELS = ['low', 'medium', 'high', 'critical'];

const capitalize = (value) => (value ? value.charAt(0).toUpperCase() + value.slice(1) : '');

const RiskAssessment = () => {
  const risk = useSelector((state) => state.complaint.riskAssessment);
  const missing = useSelector((state) => state.complaint.missingFields);

  // No assessment has run yet (fresh load, or after Reset Form) when
  // severity is null. Previously LEVELS.indexOf(null) === -1 was clamped
  // to 0 by Math.max(0, ...), which incorrectly filled the gauge's first
  // ("low") segment and implied a real assessment had already happened.
  const hasAssessment = Boolean(risk.severity);
  const severityIndex = hasAssessment ? Math.max(0, LEVELS.indexOf(risk.severity)) : -1;
  const severityClass =
    risk.severity === 'critical' ? 'risk-critical' :
    risk.severity === 'high' ? 'risk-major' :
    risk.severity === 'medium' ? 'risk-medium' :
    risk.severity === 'low' ? 'risk-minor' : '';
  const confidencePct = Math.round((risk.confidence || 0) * 100);

  return (
    <div className="risk-card">
      <h2 className="risk-header">AI Risk Assessment</h2>

      {/* Signature element: a lab-report-style severity gauge, not just an
          isolated badge -- shows where this complaint sits on the full
          low -> medium -> high -> critical scale. */}
      <div className="risk-gauge">
        <div className="risk-gauge-track">
          {LEVELS.map((level, i) => (
            <span
              key={level}
              className={\`risk-gauge-segment \${hasAssessment && i <= severityIndex ? \`filled \${severityClass}\` : ''}\`}
            />
          ))}
        </div>
        <div className="risk-gauge-labels">
          {LEVELS.map((level) => <span key={level}>{level}</span>)}
        </div>
      </div>

      <div className="risk-summary">
        <span className={\`risk-badge \${hasAssessment ? severityClass : 'risk-unassessed'}\`}>
          {hasAssessment ? \`\${capitalize(risk.severity)} Severity\` : 'Not Yet Assessed'}
        </span>
        <span className="risk-confidence">
          {hasAssessment ? <>Confidence <strong>{confidencePct}%</strong></> : 'Awaiting AI assessment'}
        </span>
      </div>

      <div className="risk-block">
        <h3 className="risk-block-title">Rationale</h3>
        <p className="risk-block-text">{risk.rationale || 'No assessment has been performed yet.'}</p>
      </div>

      <div className="risk-block">
        <h3 className="risk-block-title">Recommended Action</h3>
        <p className="risk-block-text">{risk.recommended_action || 'Submit a complaint description to generate a recommendation.'}</p>
      </div>

      {missing && missing.length > 0 && (
        <div className="missing-info-box">
          <strong>Missing Critical Info:</strong> {missing.join(', ')}
        </div>
      )}
    </div>
  );
};

export default RiskAssessment;
`);

// =============================================================================
// FRONTEND: App.css -- neutral badge tint + example chip styling
// (reuses existing design tokens only, no new colors)
// =============================================================================

patchFile('frontend/src/App.css', [
  {
    anchor: '.risk-badge.risk-minor rule',
    from: `.risk-badge.risk-minor { background-color: var(--signal-minor-tint); color: var(--signal-minor); }`,
    to: `.risk-badge.risk-minor { background-color: var(--signal-minor-tint); color: var(--signal-minor); }
.risk-badge.risk-unassessed { background-color: var(--surface-sunken); color: var(--ink-400); }`
  },
  {
    anchor: '.ai-assistant-text rule, before scrollbar comment',
    from: `.ai-assistant-text {
  margin: 0;
  font-size: 0.9rem;
  color: var(--brand-ink);
  line-height: 1.5;
}

/* Subtle, consistent scrollbars for the two independently-scrolling panes */`,
    to: `.ai-assistant-text {
  margin: 0;
  font-size: 0.9rem;
  color: var(--brand-ink);
  line-height: 1.5;
}

.example-chip {
  display: block;
  width: 100%;
  text-align: left;
  background-color: var(--surface-sunken);
  border: 1px dashed var(--line-strong);
  border-radius: var(--radius-sm);
  padding: 0.6rem 0.85rem;
  margin-bottom: var(--spacing-sm);
  cursor: pointer;
  font: inherit;
}
.example-chip:hover { border-color: var(--brand); background-color: var(--brand-tint); }
.example-chip:focus-visible { outline: 2px solid var(--brand); outline-offset: 2px; }

.example-chip-label {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  font-size: 0.72rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--brand);
  margin-bottom: 0.25rem;
}

.example-chip-icon { width: 13px; height: 13px; }

.example-chip-text {
  display: block;
  font-size: 0.85rem;
  color: var(--ink-600);
  font-style: italic;
}

/* Subtle, consistent scrollbars for the two independently-scrolling panes */`
  }
]);

console.log('\\nPhase 6 cleanup complete.');