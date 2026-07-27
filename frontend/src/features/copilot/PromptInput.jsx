
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
        ? `I've updated the complaint record. Still missing: ${result.missing_fields.join(', ')}.`
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
