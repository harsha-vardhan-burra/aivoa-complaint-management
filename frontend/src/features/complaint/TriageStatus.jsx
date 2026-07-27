import { useSelector } from 'react-redux';

// Presentational only: a controlled-document "stamp" indicating where the
// record stands. Reset now lives in the form's action row (see
// ComplaintForm), so this component owns no dispatch.
const TriageStatus = () => {
  const { triageStatus } = useSelector((state) => state.complaint);
  const isReady = triageStatus === 'Ready to Commit';

  return (
    <div className={`triage-stamp ${isReady ? 'triage-stamp-ready' : 'triage-stamp-pending'}`}>
      {triageStatus}
    </div>
  );
};

export default TriageStatus;
