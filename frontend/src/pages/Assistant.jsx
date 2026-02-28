import React from "react";
import ChatAssistant from "../components/ChatAssistant";
import ReportView from "../components/ReportView";
import BudgetGenerator from "../components/BudgetGenerator";
import LoanUploader from "../components/LoanUploader";
import TaxSuggestions from "../components/TaxSuggestions";
import AnomalyExplainer from "../components/AnomalyExplainer";

export default function Assistant() {
  return (
    <div style={{ padding: 16, display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
      <div>
        <ChatAssistant />
        <div style={{ height: 12 }} />
        <BudgetGenerator />
        <AnomalyExplainer />
      </div>
      <div>
        <ReportView />
        <LoanUploader />
        <TaxSuggestions />
      </div>
    </div>
  );
}
