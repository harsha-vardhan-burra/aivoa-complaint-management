import { useState, useRef } from "react";
import { useSelector, useDispatch } from "react-redux";
import ChatMessage from "./ChatMessage";
import PromptInput from "./PromptInput";
import {
  setUploadedDocument,
  clearUploadedDocument,
  setDraftText,
  addMessage,
  setLoading,
  setError,
} from "./copilotSlice";
import {
  setComplaint,
  setRiskAssessment,
  setMissingFields,
  setLastChangedFields,
} from "../complaint/complaintSlice";
import { processComplaintDocument } from "../../services/api";
import {
  TrayUploadIcon,
  DocumentIcon,
  CloseIcon,
  AssistantMarkIcon,
} from "../../components/icons";
import "./CopilotPanel.css";

const EXAMPLE_TEXT =
  "Apollo Pharmacy reported discolored capsules in Amoxicillin Capsules 500 mg.";

const FIELD_LABELS = {
  complaint_source: "Complaint Source",
  customer_name: "Customer Name",
  product_name: "Product Name",
  product_strength_grade: "Product Strength/Grade",
  batch_number: "Batch/Lot Number",
  manufacturing_date: "Manufacturing Date",
  expiry_date: "Expiry Date",
  quantity_affected: "Quantity Affected",
  complaint_type: "Complaint Type",
  complaint_date: "Complaint Date",
  detailed_complaint_description: "Detailed Description",
  initial_severity: "Initial Severity",
  priority: "Priority",
};

const CopilotPanel = () => {
  const messages = useSelector((state) => state.copilot.messages);
  const uploadedDocument = useSelector(
    (state) => state.copilot.uploadedDocument
  );
  const loading = useSelector((state) => state.copilot.loading);
  const currentComplaint = useSelector((state) => state.complaint.complaint);
  const currentRisk = useSelector((state) => state.complaint.riskAssessment);

  const dispatch = useDispatch();
  const fileInputRef = useRef(null);

  // Raw File object is kept outside Redux to prevent non-serializable warnings
  const [selectedFile, setSelectedFile] = useState(null);
  const [isProcessingDoc, setIsProcessingDoc] = useState(false);

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
    setSelectedFile(file);
    dispatch(setUploadedDocument({ name: file.name, size: file.size }));
    event.target.value = "";
  };

  const handleRemoveDocument = () => {
    setSelectedFile(null);
    dispatch(clearUploadedDocument());
  };

  const handleUseExample = () => {
    dispatch(setDraftText(EXAMPLE_TEXT));
  };

  const handleProcessDocument = async () => {
    if (!selectedFile || isProcessingDoc || loading) return;

    setIsProcessingDoc(true);
    dispatch(setLoading(true));
    dispatch(setError(null));

    const isExistingComplaint = Object.values(currentComplaint || {}).some(
      (val) => val !== null && val !== "" && val !== undefined
    );

    dispatch(
      addMessage({
        id: Date.now(),
        role: "user",
        content: `[Uploaded Document: ${selectedFile.name}]`,
      })
    );

    try {
      const result = await processComplaintDocument(
        selectedFile,
        currentComplaint,
        currentRisk
      );

      // Apply state ONLY on clean success
      dispatch(setComplaint(result.complaint));
      if (result.risk) {
        dispatch(setRiskAssessment(result.risk));
      }
      dispatch(setMissingFields(result.missing_fields));

      const changedFields = result.changed_fields || [];
      dispatch(setLastChangedFields(changedFields));

      let summary = "";
      if (changedFields.length === 0) {
        summary =
          "Document processed successfully, but no new complaint facts were detected.";
      } else {
        const header = isExistingComplaint
          ? `Updated complaint details from ${selectedFile.name}:`
          : `Extracted complaint details from ${selectedFile.name}:`;
        const bullets = changedFields
          .map(
            (f) =>
              `• ${FIELD_LABELS[f] || f}: ${result.complaint[f] ?? "Not provided"}`
          )
          .join("\n");
        const missingPart =
          result.missing_fields.length > 0
            ? `\n\nStill missing: ${result.missing_fields.map((f) => FIELD_LABELS[f] || f).join(", ")}.`
            : "\n\nAll key complaint fields are now captured.";

        summary = `${header}\n${bullets}${missingPart}`;
      }

      dispatch(
        addMessage({ id: Date.now() + 1, role: "assistant", content: summary })
      );

      // Clear processed document chip
      setSelectedFile(null);
      dispatch(clearUploadedDocument());
    } catch (err) {
      // REQUIREMENT 7: State preservation on error -- existing complaint/risk state left untouched
      const detail =
        err?.response?.data?.detail ||
        "Failed to process document. Please ensure it is a valid, unencrypted text PDF, TXT, or EML file.";
      dispatch(setError(detail));
      dispatch(
        addMessage({
          id: Date.now() + 1,
          role: "assistant",
          content: `⚠ Document Processing Error: ${detail}`,
        })
      );
    } finally {
      setIsProcessingDoc(false);
      dispatch(setLoading(false));
    }
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
            accept=".pdf,.txt,.eml"
            className="visually-hidden"
            onChange={handleFileChange}
            aria-hidden="true"
            tabIndex={-1}
          />
        </div>

        <div className="info-box">
          <strong>Supported formats:</strong> PDF, TXT, EML &middot; Max
          file size 10MB
        </div>

        {uploadedDocument && (
          <div className="document-chip" style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: '8px',
            padding: '8px 12px',
            marginBottom: '12px',
            backgroundColor: 'rgba(15, 110, 94, 0.1)',
            border: '1px solid rgba(15, 110, 94, 0.3)',
            borderRadius: '6px'
          }}>
            <span className="document-chip-name" style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              fontSize: '0.875rem',
              fontWeight: 500
            }}>
              <DocumentIcon className="document-chip-icon" />
              {uploadedDocument.name} ({(uploadedDocument.size / 1024).toFixed(1)} KB)
            </span>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <button
                type="button"
                className="btn-primary"
                onClick={handleProcessDocument}
                disabled={isProcessingDoc || loading}
                style={{
                  padding: '4px 10px',
                  fontSize: '0.75rem',
                  borderRadius: '4px'
                }}
              >
                {isProcessingDoc ? 'Extracting...' : 'Process Document'}
              </button>
              <button
                type="button"
                className="document-chip-remove"
                onClick={handleRemoveDocument}
                disabled={isProcessingDoc}
                aria-label={`Remove ${uploadedDocument.name}`}
              >
                <CloseIcon className="chip-remove-icon" />
              </button>
            </div>
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

