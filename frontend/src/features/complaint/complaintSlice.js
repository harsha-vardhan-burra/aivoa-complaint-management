
import { createSlice } from '@reduxjs/toolkit';

// Field names here match the backend's ComplaintBase / RiskAssessmentBase
// schemas (see backend/app/schemas) so that API responses can be stored
// directly without a translation layer. The non-destructive merge of a
// conversational edit into the existing complaint already happens
// server-side (LangGraph's merge_patch node, Phase 5) -- this slice just
// mirrors whatever the backend returns as the single source of truth.
//
// initialState is genuinely empty: no complaint has been submitted yet,
// so every field is null and no risk assessment has run. (A prior
// version of this file hardcoded a fictional "Apollo Pharmacy" complaint
// and risk assessment here as a tutorial fixture -- that leaked into
// real application state on every fresh load and every Reset Form click.
// The same example is now offered as an optional "Try an example" chip
// in CopilotPanel, which only inserts input text and runs it through the
// real pipeline -- it never writes directly to this state.)
const initialState = {
  triageStatus: "Pending Triage",
  complaint: {
    complaint_source: null,
    customer_name: null,
    product_name: null,
    product_strength_grade: null,
    batch_number: null,
    manufacturing_date: null,
    expiry_date: null,
    quantity_affected: null,
    complaint_type: null,
    complaint_date: null,
    detailed_complaint_description: null,
    initial_severity: null,
    priority: null,
  },
  riskAssessment: {
    severity: null,
    rationale: null,
    missing_fields: [],
    confidence: null,
    recommended_action: null,
  },
  missingFields: [],
};

const complaintSlice = createSlice({
  name: 'complaint',
  initialState,
  reducers: {
    // Full replace: used whenever we receive a fresh merged_complaint
    // from POST /api/ai/complaints/process. The backend already
    // performed the non-destructive merge, so the frontend does not
    // do its own patching here.
    setComplaint: (state, action) => {
      state.complaint = action.payload;
    },
    setRiskAssessment: (state, action) => {
      state.riskAssessment = action.payload;
    },
    // missing_fields comes from the AI's own risk assessment
    // (PROJECT_CONTEXT.md Data Integrity Rule 6: missing information
    // must be explicit) rather than a client-side heuristic.
    setMissingFields: (state, action) => {
      state.missingFields = action.payload;
      state.triageStatus = action.payload.length === 0 ? "Ready to Commit" : "Pending Triage";
    },
    // Returns the (now genuinely empty) initialState -- no demo data is
    // restored.
    resetComplaint: () => initialState,
  }
});

export const { setComplaint, setRiskAssessment, setMissingFields, resetComplaint } = complaintSlice.actions;
export default complaintSlice.reducer;
