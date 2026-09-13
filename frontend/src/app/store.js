
import { configureStore } from '@reduxjs/toolkit';
import complaintReducer from '../features/complaint/complaintSlice';
import copilotReducer from '../features/copilot/copilotSlice';
import aiInsightsReducer from '../features/insights/aiInsightsSlice';

export const store = configureStore({
  reducer: {
    complaint: complaintReducer,
    copilot: copilotReducer,
    aiInsights: aiInsightsReducer,
  },
});
