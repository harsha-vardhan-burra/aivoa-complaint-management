import axios from 'axios'

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  },
})

export const getHealth = async () => {
  const response = await apiClient.get('/api/health')
  return response.data
}

// Phase 6: sends one natural-language message plus whatever the frontend
// currently knows about the complaint. The backend (LangGraph, Phase 5)
// performs the non-destructive merge and returns the full merged
// complaint plus a fresh risk assessment -- the frontend does not merge
// patches itself.
export const processComplaintMessage = async (message, currentComplaint, currentRisk) => {
  const response = await apiClient.post('/api/ai/complaints/process', {
    message,
    current_complaint: currentComplaint,
    current_risk: currentRisk,
  })
  return response.data
}

// Phase 6.5: persists the current structured complaint state and optional
// AI risk assessment and decision-support insights via POST /api/complaints.
export const saveComplaint = async (complaint, riskAssessment, insights = {}) => {
  const payload = {
    complaint,
    risk_assessment: riskAssessment,
    ...insights,
  }
  const response = await apiClient.post('/api/complaints', payload)
  return response.data
}

// Feature 2: on-demand plain-language summary and key facts.
export const generateComplaintSummary = async (complaint) => {
  const response = await apiClient.post('/api/ai/complaints/summary', {
    complaint,
  })
  return response.data
}

// Feature 3: deterministic candidate duplicate check.
export const checkDuplicateComplaints = async (complaint, windowDays = 90) => {
  const response = await apiClient.post('/api/ai/complaints/duplicates', {
    complaint,
    window_days: windowDays,
  })
  return response.data
}

// Feature 4: AI root cause recommendation
export const suggestRootCause = async (complaint, risk) => {
  const response = await apiClient.post('/api/ai/complaints/root-cause', {
    complaint,
    risk,
  })
  return response.data
}

// Feature 5: AI CAPA proposal
export const suggestCapa = async (complaint, risk, rootCause = null) => {
  const response = await apiClient.post('/api/ai/complaints/capa', {
    complaint,
    risk,
    root_cause: rootCause,
  })
  return response.data
}

// Phase 8: uploads a complaint document (.pdf, .txt, .eml) along with optional
// existing complaint/risk state for non-destructive document extraction.
export const processComplaintDocument = async (file, currentComplaint, currentRisk) => {
  const formData = new FormData()
  formData.append('file', file)
  if (currentComplaint) {
    formData.append('current_complaint_json', JSON.stringify(currentComplaint))
  }
  if (currentRisk) {
    formData.append('current_risk_json', JSON.stringify(currentRisk))
  }

  const response = await apiClient.post('/api/ai/complaints/document', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })
  return response.data
}



