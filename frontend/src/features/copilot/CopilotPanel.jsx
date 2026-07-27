import { useRef } from "react";
import { useSelector, useDispatch } from "react-redux";
import ChatMessage from "./ChatMessage";
import PromptInput from "./PromptInput";
import {
  setUploadedDocument,
  clearUploadedDocument,
  setDraftText,
} from "./copilotSlice";
import {
  TrayUploadIcon,
  DocumentIcon,
  CloseIcon,
  AssistantMarkIcon,
} from "../../components/icons";
import "./CopilotPanel.css";

// Plain input text for the real pipeline -- clicking the chip below only
// ever calls setDraftText(EXAMPLE_TEXT). It never dispatches setComplaint
// or setRiskAssessment directly, never calls the API itself, and carries
// no canned response. The user still submits it through the same
// PromptInput Send button (or Enter) as anything they type themselves,
// so it goes through the real processComplaintMessage -> LangGraph ->
// Groq -> Redux pipeline.
const EXAMPLE_TEXT =
  "Apollo Pharmacy reported discolored capsules in Amoxicillin Capsules 500 mg.";

const CopilotPanel = () => {
  const messages = useSelector((state) => state.copilot.messages);
  const uploadedDocument = useSelector(
    (state) => state.copilot.uploadedDocument,
  );
  const dispatch = useDispatch();
  const fileInputRef = useRef(null);

  const handleBrowseClick = () => {
    fileInputRef.current?.click();
  };

  const handleZoneKeyDown = (event) => {
    if (event.key === "Enter" || event.key === " ") {
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
    event.target.value = "";
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
          <p className="upload-title">
            Drag &amp; drop complaint document here
          </p>
          <p className="upload-subtitle">
            or <span className="upload-link">click to browse</span>
          </p>
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
          <strong>Supported formats:</strong> PDF, DOCX, TXT, EML &middot; Max
          file size 10MB
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
              aria-label={`Remove ${uploadedDocument.name}`}
            >
              <CloseIcon className="chip-remove-icon" />
            </button>
          </div>
        )}

        <div className="ai-assistant-box">
          <AssistantMarkIcon className="ai-icon" />
          <p className="ai-assistant-text">
            Upload a complaint document or paste text above. I will
            automatically extract the details and populate the form for you.
          </p>
        </div>

        <button
          type="button"
          className="example-chip"
          onClick={handleUseExample}
          aria-label="Try an example complaint"
        >
          <span className="example-chip-label">Try an example</span>
          <span className="example-chip-text">
            &ldquo;{EXAMPLE_TEXT}&rdquo;
          </span>
        </button>

        {/* Actual Chat Messages */}
        {messages.map((msg) => (
          <ChatMessage key={msg.id} role={msg.role} content={msg.content} />
        ))}
      </div>

      {/* Fixed Bottom Input */}
      <div className="copilot-actions">
        <PromptInput />
        <div className="disclaimer">
          AI responses may contain errors. Please verify information.
        </div>
      </div>
    </div>
  );
};

export default CopilotPanel;
