
import { useDispatch, useSelector } from 'react-redux';
import { addMessage, setLoading, setError, setDraftText } from './copilotSlice';
import {
  setComplaint,
  setRiskAssessment,
  setMissingFields,
  setLastChangedFields,
} from '../complaint/complaintSlice';
import { processComplaintMessage } from '../../services/api';
import { SendIcon } from '../../components/icons';
import { FIELD_LABELS } from '../../constants/fieldLabels';

const PromptInput = ({ inputRef }) => {
  const dispatch = useDispatch();
  const text = useSelector((state) => state.copilot.draftText);
  const currentComplaint = useSelector((state) => state.complaint.complaint);
  const currentRisk = useSelector((state) => state.complaint.riskAssessment);
  const loading = useSelector((state) => state.copilot.loading);

  const handleSend = async () => {
    const trimmed = text.trim();
    if (!trimmed || loading) return;

    dispatch(addMessage({ id: Date.now(), role: 'user', content: trimmed }));
    dispatch(setDraftText(''));
    dispatch(setLoading(true));
    dispatch(setError(null));

    const isExistingComplaint = Object.values(currentComplaint || {}).some(
      (val) => val !== null && val !== '' && val !== undefined
    );

    try {
      const result = await processComplaintMessage(
        trimmed,
        currentComplaint,
        currentRisk
      );

      dispatch(setComplaint(result.complaint));
      if (result.risk) {
        dispatch(setRiskAssessment(result.risk));
      }
      dispatch(setMissingFields(result.missing_fields));

      const changedFields = result.changed_fields || [];
      dispatch(setLastChangedFields(changedFields));

      let summary = '';
      if (changedFields.length === 0) {
        if (isExistingComplaint) {
          summary = 'No new complaint facts detected. The complaint record remains unchanged.';
        } else {
          summary = 'No complaint details could be extracted from that message. Please describe the complaint facts or upload a document.';
        }
      } else {
        const header = isExistingComplaint
          ? 'Updated complaint details:'
          : 'Extracted complaint details:';
        const bullets = changedFields
          .map(
            (f) => `• ${FIELD_LABELS[f] || f}: ${result.complaint[f] ?? 'Not provided'}`
          )
          .join('\n');
        const missingPart =
          result.missing_fields.length > 0
            ? `\n\nStill missing: ${result.missing_fields.map((f) => FIELD_LABELS[f] || f).join(', ')}.`
            : '\n\nAll key complaint fields are now captured.';

        summary = `${header}\n${bullets}${missingPart}`;
      }

      dispatch(
        addMessage({ id: Date.now() + 1, role: 'assistant', content: summary })
      );
    } catch (err) {
      const message =
        err?.response?.data?.detail ||
        'Something went wrong processing that message. Please try again.';
      dispatch(setError(message));
      dispatch(
        addMessage({ id: Date.now() + 1, role: 'assistant', content: message })
      );
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
        ref={inputRef}
        rows="2"
        placeholder="Ask about this complaint, or paste details to extract..."
        value={text}
        onChange={(event) => dispatch(setDraftText(event.target.value))}
        onKeyDown={handleKeyDown}
        disabled={loading}
      />
      <button
        type="button"
        onClick={handleSend}
        disabled={!text.trim() || loading}
        aria-label="Send message"
      >
        <SendIcon className="send-icon" />
      </button>
    </div>
  );
};

export default PromptInput;

