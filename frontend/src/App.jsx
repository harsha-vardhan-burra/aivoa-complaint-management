import ComplaintForm from './features/complaint/ComplaintForm';
import RiskAssessment from './features/complaint/RiskAssessment';
import CopilotPanel from './features/copilot/CopilotPanel';
import './App.css';

function App() {
  return (
    <div className="app-container">
      <header className="app-header">
        <span className="wordmark">AIVOA</span>
        <span className="wordmark-divider" aria-hidden="true" />
        <span className="wordmark-sub">Complaint Management System</span>
      </header>
      <main className="main-content">
        <section className="left-panel">
          <ComplaintForm />
          <RiskAssessment />
        </section>
        <section className="right-panel">
          <CopilotPanel />
        </section>
      </main>
    </div>
  );
}

export default App;
