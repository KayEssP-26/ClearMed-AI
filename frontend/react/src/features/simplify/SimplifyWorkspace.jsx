import { AnimatePresence, motion } from "motion/react";
import { useRef, useState } from "react";

import { simplifyReport, simplifyText } from "../../services/api";
import { EvaluationDashboard } from "../evaluation/EvaluationDashboard";
import "./results.css";

const ACCEPTED_FILE_TYPES = ["application/pdf", "image/jpeg", "image/png"];
const ACCEPTED_FILE_EXTENSIONS = ".pdf,.jpg,.jpeg,.png";
const EXPLANATION_HEADINGS = {
  SUMMARY: "Summary",
  "WHAT IT MEANS": "What it means",
  "WHAT TO DO": "What to do",
  "TERMS EXPLAINED": "Terms explained",
};

function parseExplanation(text) {
  const normalized = text.replace(/\*\*/g, "").trim();
  const headingPattern = /^\s*(SUMMARY|WHAT IT MEANS|WHAT TO DO|TERMS EXPLAINED)\s*:\s*/gim;
  const headings = [...normalized.matchAll(headingPattern)];

  if (!headings.length) {
    return [{ key: "explanation", title: "Explanation", content: normalized }];
  }

  return headings.map((heading, index) => ({
    key: heading[1].toLowerCase().replaceAll(" ", "-"),
    title: EXPLANATION_HEADINGS[heading[1].toUpperCase()],
    content: normalized.slice(
      heading.index + heading[0].length,
      headings[index + 1]?.index ?? normalized.length,
    ).trim(),
  }));
}

function ExplanationSection({ section, index }) {
  const lines = section.content.split(/\r?\n/).map((line) => line.trim()).filter(Boolean);
  const isList = lines.length > 0 && lines.every((line) => /^(?:[-*•]|\d+[.)])\s+/.test(line));

  return <section className={`explanation-section explanation-${section.key}`} aria-labelledby={`explanation-${section.key}`}>
    <div className="explanation-section-heading"><span aria-hidden="true">{String(index + 1).padStart(2, "0")}</span><h3 id={`explanation-${section.key}`}>{section.title}</h3></div>
    {isList
      ? <ul>{lines.map((line, lineIndex) => <li key={`${lineIndex}-${line}`}>{line.replace(/^(?:[-*•]|\d+[.)])\s+/, "")}</li>)}</ul>
      : <p>{section.content}</p>}
  </section>;
}

function ReadabilityCard({ label, value, accent }) {
  return <div className="readability-card"><span>{label}</span><strong className={accent ? "readability-improved" : ""}>{Number.isFinite(value) ? value.toFixed(1) : "—"}</strong><small>Flesch reading ease</small></div>;
}

function SuggestedQuestions({ simplifiedText }) {
  const opening = simplifiedText.split(/[.!?]/).find((sentence) => sentence.trim().length > 20)?.trim();
  const questions = [
    opening ? `Can you explain what “${opening.slice(0, 110)}${opening.length > 110 ? "…" : ""}” means for me?` : "What does this result mean for me?",
    "What should I do next, and when should I follow up?",
    "Are there symptoms or changes that mean I should seek care sooner?",
    "Do any medicines, tests, or lifestyle changes need to be discussed?",
  ];
  return <aside className="questions-card" aria-labelledby="questions-title"><p className="eyebrow">Prepare for your visit</p><h3 id="questions-title">Questions to ask your doctor</h3><p>Use these as a starting point for a conversation with your care team.</p><ul>{questions.map((question) => <li key={question}>{question}</li>)}</ul></aside>;
}

function Results({ result }) {
  const gain = result.readability_after - result.readability_before;
  const explanationSections = parseExplanation(result.simplified);
  const [copied, setCopied] = useState(false);
  const copyExplanation = async () => {
    try {
      await navigator.clipboard.writeText(result.simplified);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 2000);
    } catch {
      setCopied(false);
    }
  };
  return <motion.section aria-live="polite" className="results-card" initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: .35, ease: "easeOut" }}>
    <div className="results-heading"><div><p className="eyebrow">Your explanation</p><h2>Here’s what it means</h2></div><div className="result-actions"><span className="complete-badge">Complete</span><button className="copy-button" type="button" onClick={copyExplanation}>{copied ? "Copied" : "Copy explanation"}</button></div></div>
    <div className="explanation-sections">{explanationSections.map((section, index) => <ExplanationSection key={section.key} section={section} index={index} />)}</div>
    {(Number.isFinite(result.readability_before) || Number.isFinite(result.readability_after)) && <div className="readability-grid">
      <ReadabilityCard label="Original" value={result.readability_before} />
      <ReadabilityCard label="Simplified" value={result.readability_after} accent />
      {Number.isFinite(gain) && <div className="gain-note"><span aria-hidden="true">↗</span><strong>{gain >= 0 ? "+" : ""}{gain.toFixed(1)}</strong><small>readability change</small></div>}
    </div>}
    <SuggestedQuestions simplifiedText={explanationSections.find((section) => section.key === "summary")?.content || result.simplified} />
  </motion.section>;
}

export function SimplifyWorkspace() {
  const [mode, setMode] = useState("text");
  const [text, setText] = useState("");
  const [file, setFile] = useState(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);
  const fileInputRef = useRef(null);

  const selectFile = (candidate) => {
    if (!candidate) return;
    const allowed = ACCEPTED_FILE_TYPES.includes(candidate.type) || /\.(pdf|jpe?g|png)$/i.test(candidate.name);
    if (!allowed) { setError("Choose a PDF, JPG, or PNG report."); return; }
    setError(""); setFile(candidate);
  };
  const switchMode = (nextMode) => { setMode(nextMode); setError(""); setResult(null); };
  const handleSubmit = async (event) => {
    event.preventDefault();
    if (mode === "text" && !text.trim()) { setError("Paste some clinical text before simplifying."); return; }
    if (mode === "upload" && !file) { setError("Choose a report to upload first."); return; }
    setError(""); setResult(null); setIsSubmitting(true);
    try { setResult(mode === "text" ? await simplifyText(text.trim()) : await simplifyReport(file)); }
    catch (requestError) { setError(requestError.message || "We couldn’t simplify that just now. Please try again."); }
    finally { setIsSubmitting(false); }
  };

  return <section className="workspace" id="simplify" aria-labelledby="workspace-title">
    <div className="workspace-heading"><p className="eyebrow">Start here</p><h2 id="workspace-title">Bring clarity to your report.</h2><p>Paste text or upload a report to receive a plain-English explanation.</p></div>
    <form className="simplify-panel" onSubmit={handleSubmit}>
      <div className="mode-switcher" role="tablist" aria-label="Choose input type">
        <button className={mode === "text" ? "active" : ""} type="button" role="tab" aria-selected={mode === "text"} onClick={() => switchMode("text")}>Paste text</button>
        <button className={mode === "upload" ? "active" : ""} type="button" role="tab" aria-selected={mode === "upload"} onClick={() => switchMode("upload")}>Upload report</button>
      </div>
      <AnimatePresence mode="wait" initial={false}>{mode === "text" ? <motion.div key="text" className="input-area" initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -6 }}>
        <label htmlFor="clinical-text">Medical text</label><textarea id="clinical-text" value={text} onChange={(event) => setText(event.target.value)} placeholder="Paste clinical notes, a discharge summary, or lab report text here…" rows="9" /><p className="field-note">Avoid including details you don’t need to share.</p>
      </motion.div> : <motion.div key="upload" className="input-area" initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -6 }}>
        <input ref={fileInputRef} className="visually-hidden" id="report-file" type="file" accept={ACCEPTED_FILE_EXTENSIONS} onChange={(event) => selectFile(event.target.files?.[0])} />
        <div className={`upload-dropzone ${isDragging ? "is-dragging" : ""} ${file ? "has-file" : ""}`} onDragEnter={(event) => { event.preventDefault(); setIsDragging(true); }} onDragOver={(event) => event.preventDefault()} onDragLeave={() => setIsDragging(false)} onDrop={(event) => { event.preventDefault(); setIsDragging(false); selectFile(event.dataTransfer.files?.[0]); }}>
          <span className="upload-icon" aria-hidden="true">↑</span>{file ? <><strong>{file.name}</strong><p>{Math.ceil(file.size / 1024)} KB · Ready to simplify</p></> : <><strong>Drop your report here</strong><p>PDF, JPG, or PNG</p></>}<button className="text-button" type="button" onClick={() => fileInputRef.current?.click()}>{file ? "Choose another file" : "Browse files"}</button>
        </div>
      </motion.div>}</AnimatePresence>
      <AnimatePresence>{error && <motion.p className="form-error" role="alert" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>{error}</motion.p>}</AnimatePresence>
      <button className="primary-button" disabled={isSubmitting} type="submit">{isSubmitting ? <><span className="spinner" aria-hidden="true" />Simplifying your report…</> : "Simplify report"}</button>
    </form>
    <AnimatePresence>{result && <Results result={result} />}</AnimatePresence>
    <EvaluationDashboard />
  </section>;
}
