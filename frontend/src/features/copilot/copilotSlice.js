
import { createSlice } from '@reduxjs/toolkit';

// Only the genuine assistant greeting ships in initial state. (A prior
// version of this file also hardcoded a fake user message and a fake
// assistant reply here, pre-simulating a conversation that never
// actually went through the API. Removed -- see CopilotPanel's "Try an
// example" chip for how that example complaint is now offered instead,
// as text the user can send through the real pipeline.)
const initialState = {
  messages: [
    {
      id: 1,
      role: 'assistant',
      content: "Hello! I am the AIVOA Copilot. Please describe the customer complaint or upload a document, and I will extract the details and assess the risk."
    }
  ],
  loading: false,
  error: null,
  uploadedDocument: null,
  // Backs the PromptInput textarea. Lives here (alongside the slice's
  // other compose-related UI state) rather than as PromptInput-local
  // useState so the example chip in CopilotPanel can populate it without
  // prop drilling or a new shared hook.
  draftText: ''
};

const copilotSlice = createSlice({
  name: 'copilot',
  initialState,
  reducers: {
    addMessage: (state, action) => { state.messages.push(action.payload); },
    setLoading: (state, action) => { state.loading = action.payload; },
    setError: (state, action) => { state.error = action.payload; },
    setUploadedDocument: (state, action) => { state.uploadedDocument = action.payload; },
    clearUploadedDocument: (state) => { state.uploadedDocument = null; },
    setDraftText: (state, action) => { state.draftText = action.payload; }
  }
});

export const {
  addMessage,
  setLoading,
  setError,
  setUploadedDocument,
  clearUploadedDocument,
  setDraftText
} = copilotSlice.actions;
export default copilotSlice.reducer;
