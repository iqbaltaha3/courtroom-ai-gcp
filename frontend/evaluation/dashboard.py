import streamlit as st
import pandas as pd
from .evaluator import EvaluationMetrics

def show_evaluation_dashboard():
    """Render the Metrics tab with evaluation results."""
    st.header("📊 Simulation Metrics")

    # Check if we have metrics stored in session state
    if "metrics_recorded" not in st.session_state or not st.session_state.metrics_recorded:
        st.info("Run a simulation first to see evaluation metrics.")
        return

    # Retrieve the stored metrics – we assume they were saved as `st.session_state.last_metrics`
    if "last_metrics" not in st.session_state:
        st.warning("No metrics available. Please run a simulation.")
        return

    metrics: EvaluationMetrics = st.session_state.last_metrics

    # Display key metrics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Overall Quality", f"{metrics.overall_quality_score:.1f}/100")
    col2.metric("Completeness", f"{metrics.completeness:.1f}%")
    col3.metric("Coherence", f"{metrics.coherence:.1f}%")
    col4.metric("Legal Accuracy", f"{metrics.legal_accuracy:.1f}%")

    st.subheader("⏱️ Node Execution Times")
    if metrics.node_times:
        df = pd.DataFrame({
            "Node": list(metrics.node_times.keys()),
            "Time (s)": list(metrics.node_times.values())
        })
        st.bar_chart(df.set_index("Node"))
    else:
        st.info("No node timing data available.")

    st.subheader("📋 Detailed Breakdown")
    st.json({
        "completeness": metrics.completeness,
        "coherence": metrics.coherence,
        "legal_accuracy": metrics.legal_accuracy,
        "overall_quality_score": metrics.overall_quality_score,
        "node_times": metrics.node_times
    })