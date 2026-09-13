import { createSlice } from '@reduxjs/toolkit';

const initialState = {
  summary: {
    loading: false,
    error: null,
    data: null,
    includeInSave: false,
  },
  duplicateCheck: {
    loading: false,
    error: null,
    matches: [],
    dismissed: false,
  },
  rootCause: {
    loading: false,
    error: null,
    data: null,
  },
  capa: {
    loading: false,
    error: null,
    data: null,
  },
};

const aiInsightsSlice = createSlice({
  name: 'aiInsights',
  initialState,
  reducers: {
    setSummaryLoading: (state, action) => {
      state.summary.loading = action.payload;
      if (action.payload) {
        state.summary.error = null;
      }
    },
    setSummaryData: (state, action) => {
      state.summary.data = action.payload;
      state.summary.loading = false;
      state.summary.error = null;
    },
    setSummaryError: (state, action) => {
      state.summary.error = action.payload;
      state.summary.loading = false;
    },
    setSummaryIncludeInSave: (state, action) => {
      state.summary.includeInSave = action.payload;
    },
    clearSummary: (state) => {
      state.summary = {
        loading: false,
        error: null,
        data: null,
        includeInSave: false,
      };
    },
    setDuplicateMatches: (state, action) => {
      state.duplicateCheck.matches = action.payload || [];
      state.duplicateCheck.dismissed = false;
    },
    dismissDuplicateBanner: (state) => {
      state.duplicateCheck.dismissed = true;
    },
    setRootCauseData: (state, action) => {
      state.rootCause.data = action.payload;
      state.rootCause.loading = false;
      state.rootCause.error = null;
    },
    setRootCauseLoading: (state, action) => {
      state.rootCause.loading = action.payload;
      if (action.payload) state.rootCause.error = null;
    },
    setRootCauseError: (state, action) => {
      state.rootCause.error = action.payload;
      state.rootCause.loading = false;
    },
    setCapaData: (state, action) => {
      state.capa.data = action.payload;
      state.capa.loading = false;
      state.capa.error = null;
    },
    setCapaLoading: (state, action) => {
      state.capa.loading = action.payload;
      if (action.payload) state.capa.error = null;
    },
    setCapaError: (state, action) => {
      state.capa.error = action.payload;
      state.capa.loading = false;
    },
    resetAiInsights: () => initialState,
  },
});

export const {
  setSummaryLoading,
  setSummaryData,
  setSummaryError,
  setSummaryIncludeInSave,
  clearSummary,
  setDuplicateMatches,
  dismissDuplicateBanner,
  setRootCauseData,
  setRootCauseLoading,
  setRootCauseError,
  setCapaData,
  setCapaLoading,
  setCapaError,
  resetAiInsights,
} = aiInsightsSlice.actions;

export default aiInsightsSlice.reducer;
