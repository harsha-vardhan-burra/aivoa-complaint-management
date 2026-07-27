import { useSelector, useDispatch } from 'react-redux';
import TriageStatus from './TriageStatus';
import { resetComplaint } from './complaintSlice';
import { CalendarIcon, ResetIcon } from '../../components/icons';

// The complaint form is a read-only projection of AI-extracted state.
// It is intentionally not an independent manual-entry mechanism: every
// field here is populated by the copilot (Phases 4-7), never typed
// directly by the user.
const ComplaintForm = () => {
  const complaint = useSelector((state) => state.complaint.complaint);
  const dispatch = useDispatch();

  return (
    <div className="complaint-card">
      <div className="card-header">
        <div>
          <h1 className="card-title">Complaint Record</h1>
          <p className="card-subtitle">API &amp; FPD Quality Assurance Module</p>
        </div>
        <TriageStatus />
      </div>

      <div className="complaint-form">
        {/* Section 1: Origin & Customer Details */}
        <div className="form-section">
          <h2 className="section-header"><span className="clause-tag">01</span>Origin &amp; Customer Details</h2>
          <div className="form-grid">
            <div className="form-group">
              <label>Complaint Source</label>
              <input
                type="text"
                value={complaint.complaint_source || ''}
                placeholder="Awaiting AI extraction..."
                readOnly
              />
            </div>
            <div className="form-group">
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
            <div className="form-group">
              <label>Product Name</label>
              <input
                type="text"
                value={complaint.product_name || ''}
                placeholder="Awaiting AI extraction..."
                readOnly
              />
            </div>
            <div className="form-group">
              <label>Product Strength/Grade</label>
              <input
                type="text"
                value={complaint.product_strength_grade || ''}
                placeholder="Awaiting AI extraction..."
                readOnly
              />
            </div>
            <div className="form-group">
              <label>Batch/Lot Number</label>
              <input
                type="text"
                className="mono-field"
                value={complaint.batch_number || ''}
                placeholder="Not provided"
                readOnly
              />
            </div>
            <div className="form-group">
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
            <div className="form-group">
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
            <div className="form-group">
              <label>Quantity Affected</label>
              <div className="quantity-field">
                <input
                  type="text"
                  value={complaint.quantity_affected || ''}
                  placeholder="Not provided"
                  readOnly
                />
                <span className="quantity-divider" aria-hidden="true" />
                <select className="unit-select" disabled defaultValue="Units">
                  <option>Units</option>
                  <option>kg</option>
                  <option>g</option>
                  <option>mg</option>
                  <option>ml</option>
                  <option>L</option>
                </select>
              </div>
            </div>
          </div>
        </div>

        {/* Section 3: Complaint Details */}
        <div className="form-section">
          <h2 className="section-header"><span className="clause-tag">03</span>Complaint Details</h2>
          <div className="form-grid">
            <div className="form-group">
              <label>Complaint Type</label>
              <input
                type="text"
                value={complaint.complaint_type || ''}
                placeholder="Awaiting AI extraction..."
                readOnly
              />
            </div>
            <div className="form-group">
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
            <div className="form-group full-width">
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
            <div className="form-group">
              <label>Initial Severity</label>
              <select className="select-field" disabled value={complaint.initial_severity || ''}>
                <option value="">Awaiting AI extraction...</option>
                <option value="Critical">Critical</option>
                <option value="Major">Major</option>
                <option value="Minor">Minor</option>
              </select>
            </div>
            <div className="form-group">
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
            onClick={() => dispatch(resetComplaint())}
          >
            <ResetIcon className="btn-icon" />
            Reset Form
          </button>
          <button type="button" className="btn-primary">Save Complaint</button>
        </div>
      </div>
    </div>
  );
};

export default ComplaintForm;
