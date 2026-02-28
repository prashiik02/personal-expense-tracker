import React from "react";
import ChatAssistant from "../components/ChatAssistant";
import ReportView from "../components/ReportView";
import BudgetGenerator from "../components/BudgetGenerator";
import LoanUploader from "../components/LoanUploader";
import TaxSuggestions from "../components/TaxSuggestions";
import AnomalyExplainer from "../components/AnomalyExplainer";
import IncomeAdviceCard from "../components/IncomeAdviceCard";

export default function Assistant() {
  return (
    <>
      <header className="finsight-header">
        <div>
          <div className="finsight-card-title" style={{ marginBottom: 0 }}>AI Assistant</div>
          <p style={{ fontSize: "11px", color: "var(--finsight-muted)", marginTop: "4px" }}>Reports, budget, tax tips & chat</p>
        </div>
      </header>
      <div className="finsight-main-grid" style={{ alignItems: "start" }}>
        <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
          <div className="finsight-card"><ChatAssistant /></div>
          <div className="finsight-card"><BudgetGenerator /></div>
          <div className="finsight-card"><AnomalyExplainer /></div>
        </div>
        <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
          <div className="finsight-card"><IncomeAdviceCard /></div>
          <div className="finsight-card"><ReportView /></div>
          <div className="finsight-card"><LoanUploader /></div>
          <div className="finsight-card"><TaxSuggestions /></div>
        </div>
      </div>
    </>
  );
}
