
import { useSelector } from 'react-redux';
import { FIELD_LABELS } from '../../constants/fieldLabels';

// Matches the backend's severity enum (low/medium/high/critical) so the
// gauge always reflects a real value the AI can return, rather than a
// different label set the API would have to be mapped into.
const LEVELS = ['low', 'medium', 'high', 'critical'];

const capitalize = (value) => (value ? value.charAt(0).toUpperCase() + value.slice(1) : '');

const RiskAssessment = () => {
  const risk = useSelector((state) => state.complaint.riskAssessment);
  const missing = useSelector((state) => state.complaint.missingFields);
  const completeness = useSelector((state) => state.complaint.completeness);

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

  const missingCritical = completeness?.missing_critical || [];
  const score = completeness?.score ?? 0;

  return (
    <div className="risk-card">
      <h2 className="risk-header">AI Risk Assessment</h2>

      {/* Feature 1: Complaint Completeness Progress Bar */}
      <div className="completeness-section">
        <div className="completeness-header">
          <span className="completeness-label">Completeness</span>
          <span className="completeness-score">{score}%</span>
        </div>
        <div className="completeness-bar-track">
          <div
            className="completeness-bar-fill"
            style={{ width: `${Math.min(100, Math.max(0, score))}%` }}
          />
        </div>
      </div>

      {/* Signature element: a lab-report-style severity gauge, not just an
          isolated badge -- shows where this complaint sits on the full
          low -> medium -> high -> critical scale. */}
      <div className="risk-gauge">
        <div className="risk-gauge-track">
          {LEVELS.map((level, i) => (
            <span
              key={level}
              className={`risk-gauge-segment ${hasAssessment && i <= severityIndex ? `filled ${severityClass}` : ''}`}
            />
          ))}
        </div>
        <div className="risk-gauge-labels">
          {LEVELS.map((level) => <span key={level}>{level}</span>)}
        </div>
      </div>

      <div className="risk-summary">
        <span className={`risk-badge ${hasAssessment ? severityClass : 'risk-unassessed'}`}>
          {hasAssessment ? `${capitalize(risk.severity)} Severity` : 'Not Yet Assessed'}
        </span>
        <span className="risk-confidence">
          {hasAssessment ? <>Confidence <strong>{confidencePct}%</strong></> : 'Awaiting AI assessment'}
        </span>
      </div>

      {/* Feature 6: Confidence Breakdown */}
      {hasAssessment && risk.confidence_factors && risk.confidence_factors.length > 0 && (
        <div className="confidence-factors-box">
          <span className="confidence-factors-title">Confidence Factors</span>
          <div className="confidence-factors-list">
            {risk.confidence_factors.map((factor, idx) => (
              <span key={idx} className="confidence-factor-tag">
                {factor}
              </span>
            ))}
          </div>
        </div>
      )}

      <div className="risk-block">
        <h3 className="risk-block-title">Rationale</h3>
        <p className="risk-block-text">{risk.rationale || 'No assessment has been performed yet.'}</p>
      </div>

      <div className="risk-block">
        <h3 className="risk-block-title">Recommended Action</h3>
        <p className="risk-block-text">{risk.recommended_action || 'Submit a complaint description to generate a recommendation.'}</p>
      </div>

      {missingCritical.length > 0 ? (
        <div className="missing-info-box">
          <strong>Missing Critical Info:</strong> {missingCritical.map((f) => FIELD_LABELS[f] || f).join(', ')}
        </div>
      ) : (
        missing && missing.length > 0 && (
          <div className="missing-info-box">
            <strong>Missing Critical Info:</strong> {missing.map((f) => FIELD_LABELS[f] || f).join(', ')}
          </div>
        )
      )}
    </div>
  );
};

export default RiskAssessment;
