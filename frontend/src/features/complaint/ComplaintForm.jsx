import { useState, useEffect } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import TriageStatus from './TriageStatus';
import { resetComplaint } from './complaintSlice';
import { resetCopilot } from '../copilot/copilotSlice';
import { CalendarIcon, ResetIcon } from '../../components/icons';
import { saveComplaint } from '../../services/api';
import './ComplaintForm.css';

// The complaint form is a read-only projection of AI-extracted state.
// It is intentionally not an independent manual-entry mechanism: every
// field here is populated by the copilot (Phases 4-7), never typed
// directly by the user.
const ComplaintForm = () => {
  const complaint = useSelector((state) => state.complaint.complaint);
  const riskAssessment = useSelector((state) => state.complaint.riskAssessment);
  const lastChangedFields = useSelector((state) => state.complaint.lastChangedFields);
  const dispatch = useDispatch();

  const [isSaving, setIsSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(null);
  const [saveError, setSaveError] = useState(null);
  const [highlightedFields, setHighlightedFields] = useState([]);

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
      const res = await saveComplaint(complaint, riskAssessment);
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

