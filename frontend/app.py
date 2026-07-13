import json
import os
from pathlib import Path

import altair as alt
import pandas as pd
import requests
import streamlit as st

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
_ROOT = Path(__file__).resolve().parents[1]
_EVALUATION_RESULTS_PATHS = (
    Path(os.getenv("EVALUATION_RESULTS_PATH", "")),
    Path(__file__).with_name("evaluation_results.json"),
    _ROOT / "eval" / "results.json",
)

st.set_page_config(page_title="ClearMed AI", page_icon="🩺", layout="wide")
st.title("ClearMed AI - Medical Report Simplifier")
st.caption("Translate complex clinical language into plain English - instantly.")

@st.cache_data(show_spinner=False)
def load_evaluation_results() -> tuple[dict | None, str | None]:
    """Load the most recently generated evaluation report, if available."""
    for path in _EVALUATION_RESULTS_PATHS:
        if path.is_file():
            try:
                return json.loads(path.read_text(encoding="utf-8")), None
            except (json.JSONDecodeError, OSError) as exc:
                return None, f"Could not read evaluation results: {exc}"
    return None, "Run eval/evaluate.py first to generate eval/results.json."


def _summary_value(summary: dict, key: str, entries: pd.DataFrame) -> float | None:
    """Read a reported aggregate, with a DataFrame fallback for older reports."""
    value = summary.get(key)
    if value is not None:
        return float(value)

    column_for_key = {
        "mean_rouge_l": "rouge_l",
        "mean_bert_score_f1": "bert_score_f1",
        "mean_readability_before": "readability_before",
        "mean_readability_after": "readability_after",
        "mean_readability_delta": "readability_delta",
    }.get(key)
    if column_for_key and column_for_key in entries:
        return float(entries[column_for_key].mean())
    return None


def render_evaluation_dashboard() -> None:
    """Render evaluation metrics and charts from eval/results.json."""
    st.subheader("Evaluation Dashboard")
    st.caption(
        "Benchmark results compare generated plain-English explanations with the "
        "golden-set references. Higher values are better for all displayed metrics."
    )

    if st.button("Refresh evaluation data", key="refresh_evaluation"):
        load_evaluation_results.clear()

    report, error = load_evaluation_results()
    if error:
        st.info(error)
        return

    entries = pd.DataFrame(report.get("entries", []))
    if entries.empty:
        st.warning("The evaluation report does not contain any completed entries.")
        return

    numeric_columns = [
        "id",
        "rouge_l",
        "bert_score_f1",
        "readability_before",
        "readability_after",
        "readability_delta",
    ]
    for column in numeric_columns:
        if column in entries:
            entries[column] = pd.to_numeric(entries[column], errors="coerce")
    entries = entries.sort_values("id")
    summary = report.get("summary", {})

    mean_rouge = _summary_value(summary, "mean_rouge_l", entries)
    mean_bert = _summary_value(summary, "mean_bert_score_f1", entries)
    mean_delta = _summary_value(summary, "mean_readability_delta", entries)

    # Compute spread statistics for each metric
    rouge_clean = entries["rouge_l"].dropna()
    bert_clean = entries["bert_score_f1"].dropna()
    delta_clean = entries["readability_delta"].dropna()

    metric_cases, metric_rouge, metric_bert, metric_readability = st.columns(4)
    metric_cases.metric("Cases evaluated", len(entries))
    metric_rouge.metric("Mean ROUGE-L", f"{mean_rouge:.3f}" if mean_rouge is not None else "N/A")
    metric_bert.metric("Mean BERTScore F1", f"{mean_bert:.3f}" if mean_bert is not None else "N/A")
    metric_readability.metric(
        "Mean readability gain",
        f"{mean_delta:+.1f}" if mean_delta is not None else "N/A",
    )

    # Display contextualizing captions and spread stats for each metric
    col_rouge_explain, col_bert_explain, col_delta_explain = st.columns(3)
    with col_rouge_explain:
        st.caption(
            f"Measures word overlap with reference. Low scores are normal for good paraphrases.\n"
            f"Median {rouge_clean.median():.3f} · Range {rouge_clean.min():.3f}–{rouge_clean.max():.3f}"
        )
    with col_bert_explain:
        st.caption(
            f"Measures meaning similarity, not exact wording. More informative than ROUGE-L.\n"
            f"Median {bert_clean.median():.3f} · Range {bert_clean.min():.3f}–{bert_clean.max():.3f}"
        )
    with col_delta_explain:
        st.caption(
            f"Positive = easier to read after simplification (Flesch reading-ease scale).\n"
            f"Median {delta_clean.median():+.1f} · Range {delta_clean.min():+.1f}–{delta_clean.max():+.1f}"
        )

    st.markdown("#### Readability improvement by case")
    readability_entries = entries.dropna(subset=["readability_before", "readability_after"])
    if not readability_entries.empty:
        lower = min(
            readability_entries["readability_before"].min(),
            readability_entries["readability_after"].min(),
        )
        upper = max(
            readability_entries["readability_before"].max(),
            readability_entries["readability_after"].max(),
        )
        diagonal = pd.DataFrame({"score": [lower, upper]})
        baseline = alt.Chart(diagonal).mark_line(color="#9ca3af", strokeDash=[5, 5]).encode(
            x=alt.X("score:Q", title="Original readability"),
            y=alt.Y("score:Q", title="Simplified readability"),
        )
        points = alt.Chart(readability_entries).mark_circle(size=70, color="#0ea5e9").encode(
            x=alt.X("readability_before:Q", title="Original readability"),
            y=alt.Y("readability_after:Q", title="Simplified readability"),
            tooltip=[
                alt.Tooltip("id:Q", title="Case"),
                alt.Tooltip("readability_before:Q", title="Before", format=".1f"),
                alt.Tooltip("readability_after:Q", title="After", format=".1f"),
                alt.Tooltip("readability_delta:Q", title="Change", format="+.1f"),
            ],
        )
        st.altair_chart((baseline + points).properties(height=330), use_container_width=True)
        st.caption("Each point is a case. X and Y axes show readability before and after simplification. Points above the dashed line improved (easier to read); points below got harder to read and may indicate regressions.")

    chart_left, chart_right = st.columns(2)
    with chart_left:
        st.markdown("#### Readability-gain distribution")
        if "readability_delta" in entries:
            delta_chart = alt.Chart(entries.dropna(subset=["readability_delta"])).mark_bar(
                color="#22c55e"
            ).encode(
                x=alt.X("readability_delta:Q", bin=alt.Bin(maxbins=12), title="Readability gain"),
                y=alt.Y("count():Q", title="Cases"),
                tooltip=[alt.Tooltip("count():Q", title="Cases")],
            ).properties(height=260)
            st.altair_chart(delta_chart, use_container_width=True)
            st.caption("Shows how consistent readability improvement is across cases. A wide spread means some cases barely improved while others improved significantly—not just an average.")
    with chart_right:
        st.markdown("#### Semantic vs. lexical similarity")
        semantic_entries = entries.dropna(subset=["rouge_l", "bert_score_f1"])
        if not semantic_entries.empty:
            similarity_chart = alt.Chart(semantic_entries).mark_circle(size=70, color="#8b5cf6").encode(
                x=alt.X("rouge_l:Q", title="ROUGE-L (word overlap)"),
                y=alt.Y("bert_score_f1:Q", title="BERTScore F1 (meaning similarity)"),
                tooltip=[
                    alt.Tooltip("id:Q", title="Case"),
                    alt.Tooltip("rouge_l:Q", title="ROUGE-L", format=".3f"),
                    alt.Tooltip("bert_score_f1:Q", title="BERT F1", format=".3f"),
                ],
            ).properties(height=260)
            st.altair_chart(similarity_chart, use_container_width=True)
            st.caption("High BERTScore + low ROUGE-L = good paraphrase (different words, same meaning). Low BERTScore is worth investigating regardless of ROUGE-L.")

    st.markdown("#### Per-case results")
    display_columns = [
        column
        for column in [
            "id",
            "rouge_l",
            "bert_score_f1",
            "readability_before",
            "readability_after",
            "readability_delta",
        ]
        if column in entries
    ]
    # Sort by BERT F1 ascending (worst-first) for easy identification of problem cases
    display_data = entries[display_columns].sort_values("bert_score_f1", ascending=True) if "bert_score_f1" in display_columns else entries[display_columns]
    st.dataframe(
        display_data,
        column_config={
            "id": st.column_config.NumberColumn("Case", format="%d"),
            "rouge_l": st.column_config.NumberColumn("ROUGE-L", format="%.3f"),
            "bert_score_f1": st.column_config.NumberColumn("BERT F1", format="%.3f"),
            "readability_before": st.column_config.NumberColumn("Before", format="%.1f"),
            "readability_after": st.column_config.NumberColumn("After", format="%.1f"),
            "readability_delta": st.column_config.NumberColumn("Gain", format="%+.1f"),
        },
        hide_index=True,
        use_container_width=True,
    )

    selected_id = st.selectbox("Inspect a benchmark case", entries["id"].astype(int).tolist())
    selected = entries.loc[entries["id"] == selected_id].iloc[0]
    with st.expander(f"Case {selected_id}: generated answer and reference"):
        st.markdown("**Generated simplification**")
        st.write(selected.get("simplified_text", "Not available."))
        st.markdown("**Golden reference**")
        st.write(selected.get("reference_simple", "Not available."))

    bert_model = summary.get("bert_score_model")
    if bert_model:
        st.caption(f"BERTScore model: `{bert_model}`")


def display_simplify_output(result: dict) -> None:
    """Render the structured response from /simplify or /simplify-report."""
    simplified_text = result.get("simplified", "")
    source_chunks = result.get("sources", [])

    st.success(simplified_text)

    fk_before = result.get("readability_before")
    fk_after = result.get("readability_after")
    if fk_before is not None or fk_after is not None:
        col1, col2 = st.columns(2)
        col1.metric(
            label="Readability (original)",
            value=f"{fk_before:.1f}" if fk_before is not None else "N/A",
        )
        col2.metric(
            label="Readability (simplified)",
            value=f"{fk_after:.1f}" if fk_after is not None else "N/A",
            delta=(
                f"{fk_after - fk_before:.1f}"
                if fk_before is not None and fk_after is not None
                else None
            ),
        )

    if source_chunks:
        with st.expander("Source Chunks Used for Simplification"):
            for i, chunk in enumerate(source_chunks, start=1):
                st.markdown(f"**Chunk {i}**")
                st.write(chunk)


tab_text, tab_upload, tab_evaluation = st.tabs(
    ["Paste Text", "Upload Report", "Evaluation"]
)

# ── Tab 1: Paste Text ──────────────────────────────────────────────────────────
with tab_text:
    clinical_text = st.text_area(
        "Enter clinical text",
        height=200,
        placeholder="Paste your clinical notes, discharge summary, or lab report here…",
    )

    if st.button("Simplify", key="btn_simplify_text"):
        if not clinical_text.strip():
            st.warning("Please enter some clinical text before simplifying.")
        else:
            with st.spinner("Simplifying…"):
                try:
                    response = requests.post(
                        f"{BACKEND_URL}/simplify",
                        json={"text": clinical_text},
                        timeout=60,
                    )
                    response.raise_for_status()
                    result = response.json()
                    st.subheader("Simplified Text")
                    display_simplify_output(result)
                except requests.exceptions.HTTPError as exc:
                    try:
                        detail = exc.response.json().get("detail", str(exc))
                    except Exception:
                        detail = str(exc)
                    st.error(f"Server error: {detail}")
                except requests.exceptions.RequestException as exc:
                    st.error(f"Could not reach the backend: {exc}")

# ── Tab 2: Upload Report ───────────────────────────────────────────────────────
with tab_upload:
    uploaded_file = st.file_uploader(
        "Upload a medical report",
        type=["pdf", "jpg", "jpeg", "png"],
        help="Supported formats: PDF, JPG, PNG",
    )

    if st.button("Simplify Report", key="btn_simplify_upload"):
        if uploaded_file is None:
            st.warning("Please upload a file before simplifying.")
        else:
            with st.spinner("Processing report…"):
                try:
                    files = {
                        "file": (
                            uploaded_file.name,
                            uploaded_file.getvalue(),
                            uploaded_file.type,
                        )
                    }
                    response = requests.post(
                        f"{BACKEND_URL}/simplify-report",
                        files=files,
                        timeout=120,
                    )
                    response.raise_for_status()
                    result = response.json()

                    st.subheader("Simplified Text")
                    display_simplify_output(result)
                except requests.exceptions.HTTPError as exc:
                    try:
                        detail = exc.response.json().get("detail", str(exc))
                    except Exception:
                        detail = str(exc)
                    st.error(f"Server error: {detail}")
                except requests.exceptions.RequestException as exc:
                    st.error(f"Could not reach the backend: {exc}")


with tab_evaluation:
    render_evaluation_dashboard()

st.markdown("---")
st.markdown(
    "**⚠️ Disclaimer:** ClearMed AI is for educational and informational purposes only. "
    "AI-generated explanations may be inaccurate, incomplete, or outdated. "
    "Always consult a qualified healthcare professional before making any medical decisions. "
    "Do not rely on this tool for emergencies or diagnosis."
)
