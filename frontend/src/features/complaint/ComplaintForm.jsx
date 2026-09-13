import { useState, useEffect } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import TriageStatus from './TriageStatus';
import { resetComplaint } from './complaintSlice';
import { resetCopilot } from '../copilot/copilotSlice';
import {
  setSummaryLoading,
  setSummaryData,
  setSummaryError,
  setSummaryIncludeInSave,
  setDuplicateMatches,
  dismissDuplicateBanner,
  setRootCauseLoading,
  setRootCauseData,
  setRootCauseError,
  setCapaLoading,
  setCapaData,
  setCapaError,
  resetAiInsights,
} from '../insights/aiInsightsSlice';
import { CalendarIcon, ResetIcon } from '../../components/icons';
import {
  saveComplaint,
  generateComplaintSummary,
  checkDuplicateComplaints,
  suggestRootCause,
  suggestCapa,
} from '../../services/api';
import './ComplaintForm.css';

// The complaint form is a read-only projection of AI-extracted state.
// It is intentionally not an independent manual-entry mechanism: every
// field here is populated by the copilot (Phases 4-7), never typed
// directly by the user.
const ComplaintForm = () => {
  const complaint = useSelector((state) => state.complaint.complaint);
  const riskAssessment = useSelector((state) => state.complaint.riskAssessment);
  const lastChangedFields = useSelector((state) => state.complaint.lastChangedFields);
  const completeness = useSelector((state) => state.complaint.completeness);
  const summary = useSelector((state) => state.aiInsights.summary);
  const duplicateCheck = useSelector((state) => state.aiInsights.duplicateCheck);
  const rootCause = useSelector((state) => state.aiInsights.rootCause);
  const capa = useSelector((state) => state.aiInsights.capa);
  const dispatch = useDispatch();

  const [isSaving, setIsSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(null);
  const [saveError, setSaveError] = useState(null);
  const [highlightedFields, setHighlightedFields] = useState([]);

  const canSummarize = (completeness?.score ?? 0) > 30;
  const canSuggestRootCause = Boolean(
    complaint.complaint_type && complaint.detailed_complaint_description
  );
  const canSuggestCapa = ['high', 'critical'].includes((riskAssessment?.severity || '').toLowerCase());

  const handleSummarize = async () => {
    if (!canSummarize || summary.loading) return;
    dispatch(setSummaryLoading(true));
    try {
      const data = await generateComplaintSummary(complaint);
      dispatch(setSummaryData(data));
    } catch (err) {
      const detail = err.response?.data?.detail || err.message || 'Failed to generate summary.';
      dispatch(setSummaryError(typeof detail === 'string' ? detail : JSON.stringify(detail)));
    }
  };

  const handleSuggestRootCause = async () => {
    if (!canSuggestRootCause || rootCause.loading) return;
    dispatch(setRootCauseLoading(true));
    try {
      const data = await suggestRootCause(complaint, riskAssessment);
      dispatch(setRootCauseData(data));
    } catch (err) {
      const detail = err.response?.data?.detail || err.message || 'Failed to suggest root cause.';
      dispatch(setRootCauseError(typeof detail === 'string' ? detail : JSON.stringify(detail)));
    }
  };

  const handleSuggestCapa = async () => {
    if (!canSuggestCapa || capa.loading) return;
    dispatch(setCapaLoading(true));
    try {
      const data = await suggestCapa(complaint, riskAssessment, rootCause?.data);
      dispatch(setCapaData(data));
    } catch (err) {
      const detail = err.response?.data?.detail || err.message || 'Failed to suggest CAPA.';
      dispatch(setCapaError(typeof detail === 'string' ? detail : JSON.stringify(detail)));
    }
  };

  useEffect(() => {
    if (lastChangedFields && lastChangedFields.length > 0) {
      setHighlightedFields(lastChangedFields);
      const timer = setTimeout(() => {
        setHighlightedFields([]);
      }, 2500);
      return () => clearTimeout(timer);
    } else {
      setHighlightedFields([]);
    }
  }, [lastChangedFields]);

  const hasMeaningfulField = Object.values(complaint || {}).some(
    (val) => val !== null && val !== '' && val !== undefined
  );

  const handleSave = async () => {
    if (!hasMeaningfulField) {
      setSaveError('Cannot save an empty complaint. Please provide complaint information via the Copilot.');
      setSaveSuccess(null);
      return;
    }

    setIsSaving(true);
    setSaveSuccess(null);
    setSaveError(null);

    try {
      // Feature 3: Deterministic candidate duplicate check pre-save (non-blocking)
      try {
        const dupRes = await checkDuplicateComplaints(complaint);
        if (dupRes && dupRes.matches && dupRes.matches.length > 0) {
          dispatch(setDuplicateMatches(dupRes.matches));
        }
      } catch (dupErr) {
        // Non-blocking: fail-open if duplicate check fails
      }

      const insights = {};
      if (summary.includeInSave && summary.data) {
        insights.summary = summary.data;
      }
      if (rootCause.data) {
        insights.root_cause = rootCause.data;
      }
      if (capa.data) {
        insights.capa = capa.data;
      }
      const res = await saveComplaint(complaint, riskAssessment, insights);
      setSaveSuccess(`Complaint persisted successfully! (ID: ${res.id})`);
    } catch (err) {
      const detail = err.response?.data?.detail || err.message || 'Failed to save complaint.';
      setSaveError(typeof detail === 'string' ? detail : JSON.stringify(detail));
    } finally {
      setIsSaving(false);
    }
  };

  const handleReset = () => {
    dispatch(resetComplaint());
    dispatch(resetCopilot());
    dispatch(resetAiInsights());
    setSaveSuccess(null);
    setSaveError(null);
    setHighlightedFields([]);
  };

  const getGroupClass = (fieldName, extraClass = '') => {
    const isHighlighted = highlightedFields.includes(fieldName);
    return `form-group ${extraClass} ${isHighlighted ? 'field-highlight-pulse' : ''}`.trim();
  };

  return (
    <div className="complaint-card">
      <div className="card-header">
        <div>
          <h1 className="card-title">Complaint Record</h1>
          <p className="card-subtitle">API &amp; FDF Quality Assurance Module</p>
        </div>
        <TriageStatus />
      </div>

      <div className="complaint-form">
        {saveSuccess && (
          <div className="alert-banner alert-success">
            ✓ {saveSuccess}
          </div>
        )}

        {saveError && (
          <div className="alert-banner alert-error">
            ⚠ {saveError}
          </div>
        )}

        {/* Feature 3: Duplicate Complaint Non-Blocking Warning Banner */}
        {duplicateCheck.matches && duplicateCheck.matches.length > 0 && !duplicateCheck.dismissed && (
          <div className="alert-banner alert-warning duplicate-banner">
            <div className="duplicate-banner-content">
              <span className="duplicate-banner-title">⚠ Potential Duplicate Detected:</span>
              {duplicateCheck.matches.map((match, idx) => (
                <span key={idx} className="duplicate-banner-item">
                  This looks similar to complaint #{String(match.complaint_id).slice(0, 8)} ({match.reason === 'same_batch_and_product' ? 'same batch & product' : 'similar description'}{match.created_at ? `, filed ${new Date(match.created_at).toLocaleDateString()}` : ''}).
                </span>
              ))}
            </div>
            <button
              type="button"
              className="btn-dismiss"
              onClick={() => dispatch(dismissDuplicateBanner())}
            >
              Dismiss
            </button>
          </div>
        )}

        {/* AI Decision Support Actions */}
        <div className="insights-actions-row">
          <button
            type="button"
            className="btn-summarize"
            onClick={handleSummarize}
            disabled={!canSummarize || summary.loading}
            title={!canSummarize ? 'Complete at least 30% of complaint fields to generate a summary' : ''}
          >
            {summary.loading ? 'Generating Summary...' : 'Summarize Complaint'}
          </button>
          <button
            type="button"
            className="btn-secondary-ai"
            onClick={handleSuggestRootCause}
            disabled={!canSuggestRootCause || rootCause.loading}
            title={!canSuggestRootCause ? 'Requires Complaint Type and Detailed Description to propose root cause' : ''}
          >
            {rootCause.loading ? 'Proposing Root Cause...' : 'Suggest Root Cause'}
          </button>
          <button
            type="button"
            className="btn-secondary-ai"
            onClick={handleSuggestCapa}
            disabled={!canSuggestCapa || capa.loading}
            title={!canSuggestCapa ? 'CAPA suggestions are only available for High or Critical severity complaints' : ''}
          >
            {capa.loading ? 'Drafting CAPA...' : 'Suggest CAPA'}
          </button>
        </div>

        {summary.error && (
          <div className="alert-banner alert-error">
            ⚠ Summary Error: {summary.error}
          </div>
        )}

        {rootCause.error && (
          <div className="alert-banner alert-error">
            ⚠ Root Cause Error: {rootCause.error}
          </div>
        )}

        {capa.error && (
          <div className="alert-banner alert-error">
            ⚠ CAPA Error: {capa.error}
          </div>
        )}

        {summary.data && (
          <div className="summary-card">
            <div className="summary-card-header">
              <h3 className="summary-card-title">Executive Summary</h3>
              <label className="summary-optin-label">
                <input
                  type="checkbox"
                  checked={summary.includeInSave}
                  onChange={(e) => dispatch(setSummaryIncludeInSave(e.target.checked))}
                />
                <span>Save summary with record</span>
              </label>
            </div>
            <p className="summary-text">{summary.data.summary}</p>
            {summary.data.key_facts && summary.data.key_facts.length > 0 && (
              <ul className="summary-facts-list">
                {summary.data.key_facts.map((fact, idx) => (
                  <li key={idx}>{fact}</li>
                ))}
              </ul>
            )}
          </div>
        )}

        {rootCause.data && (
          <div className="insight-card root-cause-card">
            <div className="insight-card-header">
              <div className="insight-title-group">
                <h3 className="insight-card-title">Root Cause Hypothesis</h3>
                <span className="ai-disclaimer-pill">AI Suggestion — not a finding</span>
              </div>
              <span className={`confidence-chip confidence-${rootCause.data.confidence}`}>
                {rootCause.data.confidence} confidence
              </span>
            </div>
            <p className="insight-hypothesis">{rootCause.data.hypothesis}</p>
            {rootCause.data.contributing_factors && rootCause.data.contributing_factors.length > 0 && (
              <>
                <div className="insight-subheading">Contributing Factors</div>
                <ul className="insight-bullets">
                  {rootCause.data.contributing_factors.map((factor, idx) => (
                    <li key={idx}>{factor}</li>
                  ))}
                </ul>
              </>
            )}
            {rootCause.data.recommended_investigation_steps && rootCause.data.recommended_investigation_steps.length > 0 && (
              <>
                <div className="insight-subheading">Recommended Investigation Steps</div>
                <ul className="insight-bullets">
                  {rootCause.data.recommended_investigation_steps.map((step, idx) => (
                    <li key={idx}>{step}</li>
                  ))}
                </ul>
              </>
            )}
          </div>
        )}

        {capa.data && (
          <div className="insight-card capa-card">
            <div className="insight-card-header">
              <div className="insight-title-group">
                <h3 className="insight-card-title">Corrective &amp; Preventive Action (CAPA)</h3>
                <span className="ai-disclaimer-pill">AI-Suggested Draft — requires QA sign-off</span>
              </div>
            </div>
            {capa.data.rationale && (
              <p className="insight-hypothesis">{capa.data.rationale}</p>
            )}
            {capa.data.corrective_actions && capa.data.corrective_actions.length > 0 && (
              <>
                <div className="insight-subheading">Corrective Actions (Immediate)</div>
                <ul className="insight-bullets">
                  {capa.data.corrective_actions.map((act, idx) => (
                    <li key={idx}>{act}</li>
                  ))}
                </ul>
              </>
            )}
            {capa.data.preventive_actions && capa.data.preventive_actions.length > 0 && (
              <>
                <div className="insight-subheading">Preventive Actions (Systemic)</div>
                <ul className="insight-bullets">
                  {capa.data.preventive_actions.map((act, idx) => (
                    <li key={idx}>{act}</li>
                  ))}
                </ul>
              </>
            )}
          </div>
        )}

        {/* Section 1: Origin & Customer Details */}
        <div className="form-section">
          <h2 className="section-header"><span className="clause-tag">01</span>Origin &amp; Customer Details</h2>
          <div className="form-grid">
            <div className={getGroupClass('complaint_source')}>
              <label>Complaint Source</label>
              <input
                type="text"
                value={complaint.complaint_source || ''}
                placeholder="Awaiting AI extraction..."
                readOnly
              />
            </div>
            <div className={getGroupClass('customer_name')}>
              <label>Customer Name</label>
              <input
                type="text"
                value={complaint.customer_name || ''}
                placeholder="Awaiting AI extraction..."
                readOnly
              />
            </div>
          </div>
        </div>

        {/* Section 2: Product & Batch Identification */}
        <div className="form-section">
          <h2 className="section-header"><span className="clause-tag">02</span>Product &amp; Batch Identification</h2>
          <div className="form-grid">
            <div className={getGroupClass('product_name')}>
              <label>Product Name</label>
              <input
                type="text"
                value={complaint.product_name || ''}
                placeholder="Awaiting AI extraction..."
                readOnly
              />
            </div>
            <div className={getGroupClass('product_strength_grade')}>
              <label>Product Strength/Grade</label>
              <input
                type="text"
                value={complaint.product_strength_grade || ''}
                placeholder="Awaiting AI extraction..."
                readOnly
              />
            </div>
            <div className={getGroupClass('batch_number')}>
              <label>Batch/Lot Number</label>
              <input
                type="text"
                className="mono-field"
                value={complaint.batch_number || ''}
                placeholder="Not provided"
                readOnly
              />
            </div>
            <div className={getGroupClass('manufacturing_date')}>
              <label>Manufacturing Date</label>
              <div className="date-field">
                <input
                  type="text"
                  value={complaint.manufacturing_date || ''}
                  placeholder="Not provided"
                  readOnly
                />
                <CalendarIcon className="date-field-icon" />
              </div>
            </div>
            <div className={getGroupClass('expiry_date')}>
              <label>Expiry Date</label>
              <div className="date-field">
                <input
                  type="text"
                  value={complaint.expiry_date || ''}
                  placeholder="Not provided"
                  readOnly
                />
                <CalendarIcon className="date-field-icon" />
              </div>
            </div>
            <div className={getGroupClass('quantity_affected')}>
              <label>Quantity Affected</label>
              <div className="quantity-field">
                <input
                  type="text"
                  value={complaint.quantity_affected || ''}
                  placeholder="Not provided"
                  readOnly
                />
                <span className="quantity-divider" aria-hidden="true" />
                <select
                  className="unit-select"
                  disabled
                  value={complaint.quantity_unit || 'Units'}
                >
                  <option value="Units">Units</option>
                  <option value="kg">kg</option>
                  <option value="g">g</option>
                  <option value="mg">mg</option>
                  <option value="ml">ml</option>
                  <option value="L">L</option>
                </select>
              </div>
            </div>
          </div>
        </div>

        {/* Section 3: Complaint Details */}
        <div className="form-section">
          <h2 className="section-header"><span className="clause-tag">03</span>Complaint Details</h2>
          <div className="form-grid">
            <div className={getGroupClass('complaint_type')}>
              <label>Complaint Type</label>
              <input
                type="text"
                value={complaint.complaint_type || ''}
                placeholder="Awaiting AI extraction..."
                readOnly
              />
            </div>
            <div className={getGroupClass('complaint_date')}>
              <label>Complaint Date</label>
              <div className="date-field">
                <input
                  type="text"
                  value={complaint.complaint_date || ''}
                  placeholder="Awaiting AI extraction..."
                  readOnly
                />
                <CalendarIcon className="date-field-icon" />
              </div>
            </div>
            <div className={getGroupClass('detailed_complaint_description', 'full-width')}>
              <label>Detailed Complaint Description</label>
              <textarea
                rows="3"
                value={complaint.detailed_complaint_description || ''}
                placeholder="Awaiting AI extraction..."
                readOnly
              />
            </div>
          </div>
        </div>

        {/* Section 4: Initial Assessment & Priority */}
        <div className="form-section">
          <h2 className="section-header"><span className="clause-tag">04</span>Initial Assessment &amp; Priority</h2>
          <div className="form-grid">
            <div className={getGroupClass('initial_severity')}>
              <label>Initial Severity</label>
              <select className="select-field" disabled value={complaint.initial_severity || ''}>
                <option value="">Awaiting AI extraction...</option>
                <option value="Critical">Critical</option>
                <option value="Major">Major</option>
                <option value="Minor">Minor</option>
              </select>
            </div>
            <div className={getGroupClass('priority')}>
              <label>Priority</label>
              <select className="select-field" disabled value={complaint.priority || ''}>
                <option value="">Awaiting AI extraction...</option>
                <option value="High">High</option>
                <option value="Medium">Medium</option>
                <option value="Low">Low</option>
              </select>
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="form-actions">
          <button
            type="button"
            className="btn-ghost"
            onClick={handleReset}
          >
            <ResetIcon className="btn-icon" />
            Reset Form
          </button>
          <button
            type="button"
            className="btn-primary"
            onClick={handleSave}
            disabled={isSaving || !hasMeaningfulField}
          >
            {isSaving ? 'Saving...' : 'Save Complaint'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default ComplaintForm;

