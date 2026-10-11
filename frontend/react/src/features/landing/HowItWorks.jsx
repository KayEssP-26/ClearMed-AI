const steps = [
  ["01", "Share a report", "Paste medical text or upload a PDF, JPG, or PNG report."],
  ["02", "Get clear context", "We translate unfamiliar wording into easier-to-follow language."],
  ["03", "Talk it through", "Use the explanation to shape questions for your healthcare professional."],
];

export function HowItWorks() {
  return (
    <section className="how-it-works" id="how-it-works" aria-labelledby="how-title">
      <div className="section-heading">
        <p className="eyebrow">Simple by design</p>
        <h2 id="how-title">Clarity starts with context.</h2>
      </div>
      <ol className="steps-list">
        {steps.map(([number, title, description]) => (
          <li key={number}>
            <span className="step-number">{number}</span>
            <div><h3>{title}</h3><p>{description}</p></div>
          </li>
        ))}
      </ol>
    </section>
  );
}
