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
export const processComplaintMessage = async (message, currentComplaint) => {
  const response = await apiClient.post('/api/ai/complaints/process', {
    message,
    current_complaint: currentComplaint,
  })
  return response.data
}
