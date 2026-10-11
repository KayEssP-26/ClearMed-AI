import "./evaluation.css";
import "./charts.css";

// This is a deliberately fixed benchmark snapshot for the public product UI.
// Update it only when the team explicitly publishes a new evaluation baseline.
const BENCHMARK = {
  summary: { mean_rouge_l: 0.106369, mean_bert_score_f1: 0.690118, mean_readability_delta: 47.2638 },
  entries: [
    [.096203,.679480,-27.01,55.13],[.067797,.641347,34.26,61.67],[.183673,.731133,16.49,55.74],[.108747,.699993,12.26,59.13],[.101167,.701901,26.81,65.66],[.086514,.659069,-15.50,59.43],[.147541,.718104,-7.04,63.29],[.080605,.669553,24.78,52.09],[.164794,.736561,23.77,53.61],[.141732,.723349,29.18,77.27],
    [.063158,.667841,-16.51,53.61],[.158730,.752353,-36.82,46.47],[.113879,.706176,33.24,59.98],[.118812,.693113,14.29,57.87],[.159624,.708143,24.44,63.29],[.068602,.638684,34.26,49.75],[.088889,.683448,36.28,60.45],[.096045,.675350,-45.28,46.47],[.131687,.718413,29.52,53.92],[.051414,.647829,-42.23,63.09],
    [.081340,.661794,29.86,55.47],[.186992,.728902,-.61,43.43],[.116279,.718542,13.95,52.19],[.107438,.685321,20.04,54.32],[.096296,.715059,16.32,57.06],[.135021,.695999,-92.99,43.53],[.086022,.681829,-1.96,39.03],[.137652,.698874,18.35,54.83],[.055696,.622858,18.35,43.43],[.143939,.719376,5.49,68.60],
    [.151261,.744051,15.31,60.85],[.112903,.707789,-11.44,61.36],[.059406,.677946,30.87,53.41],[.102439,.688084,22.41,59.74],[.072993,.640820,-3.99,35.88],[.080000,.680847,29.86,67.38],[.045918,.598252,3.46,53.44],[.140000,.748180,-43.25,59.03],[.092486,.689198,10.91,50.67],[.091168,.684393,-43.25,53.00],
    [.097087,.719080,-9.41,50.97],[.127820,.688184,20.38,50.26],[.121622,.704757,54.39,63.39],[.068182,.666765,-10.42,54.52],[.126482,.705518,44.75,57.10],[.074667,.671609,21.40,52.09],[.060606,.642880,34.26,43.12],[.101333,.674005,27.83,53.81],[.134831,.729893,31.89,57.91],[.080952,.663279,-6.02,51.38],
  ].map(([rouge_l, bert_score_f1, readability_before, readability_after], index) => ({ id: index + 1, rouge_l, bert_score_f1, readability_before, readability_after, readability_delta: readability_after - readability_before })),
};

const number = (value, digits = 1) => Number.isFinite(Number(value)) ? Number(value).toFixed(digits) : "—";

function Stat({ label, value, note }) {
  return <div className="benchmark-stat"><span>{label}</span><strong>{value}</strong>{note && <small>{note}</small>}</div>;
}

function ReadabilityDistribution({ entries }) {
  const binSize = 20;
  const min = 0;
  const max = 140;
  const bins = Array.from({ length: 7 }, (_, index) => ({ start: min + index * binSize, count: 0 }));
  entries.forEach((entry) => {
    const index = Math.min(bins.length - 1, Math.max(0, Math.floor(Number(entry.readability_delta) / binSize)));
    bins[index].count += 1;
  });
  const highest = Math.max(...bins.map((bin) => bin.count), 1);
  return <div className="distribution-chart" role="img" aria-label="Distribution of readability gains across benchmark cases">
    {bins.map((bin) => <div className="distribution-bin" key={bin.start}><span className="distribution-count">{bin.count || ""}</span><i style={{ height: `${(bin.count / highest) * 100}%` }} /><small>{bin.start}–{bin.start + binSize}</small></div>)}
  </div>;
}

function SimilarityPlot({ entries }) {
  const maximumGain = Math.max(...entries.map((entry) => Number(entry.readability_delta)), 1);
  return <div className="similarity-plot" role="img" aria-label="Plot of readability gain and BERTScore for every evaluation case">
    <span className="plot-y-label">Meaning similarity</span><span className="plot-x-label">Readability gain</span>
    {entries.map((entry) => <i key={entry.id} className="plot-point" title={`Case ${entry.id}: readability gain ${number(entry.readability_delta)}, BERT F1 ${number(entry.bert_score_f1, 3)}`} style={{ left: `${Math.max(3, (Number(entry.readability_delta) / maximumGain) * 100)}%`, bottom: `${Math.max(3, Number(entry.bert_score_f1) * 100)}%` }} />)}
  </div>;
}

export function EvaluationDashboard() {
  const { entries, summary } = BENCHMARK;
  const readabilityGain = summary.mean_readability_delta ?? (entries.reduce((total, entry) => total + (Number(entry.readability_delta) || 0), 0) / Math.max(entries.length, 1));
  return <section className="benchmark-section" aria-labelledby="benchmark-title">
    <div className="benchmark-heading"><div><p className="eyebrow">Evaluation dashboard</p><h2 id="benchmark-title">Quality, measured over time.</h2><p>Benchmark results compare ClearMed explanations with reviewed plain-language references.</p></div><span className="case-count">{entries.length} cases evaluated</span></div>
    <div className="benchmark-stats"><Stat label="Mean ROUGE-L" value={number(summary.mean_rouge_l, 3)} note="Word overlap" /><Stat label="Mean BERTScore F1" value={number(summary.mean_bert_score_f1, 3)} note="Meaning similarity" /><Stat label="Readability gain" value={`${Number(readabilityGain) >= 0 ? "+" : ""}${number(readabilityGain)}`} note="Flesch reading ease" /></div>
    {entries.length > 0 && <div className="chart-grid"><article className="chart-card"><div className="chart-title"><h3>How consistently clarity improved</h3></div><ReadabilityDistribution entries={entries} /><p>Each bar shows how many reports achieved a given readability gain. Most improvements are positive.</p></article><article className="chart-card"><div className="chart-title"><h3>Clarity with meaning preserved</h3></div><SimilarityPlot entries={entries} /><p>Points toward the upper-right are clearer explanations with stronger meaning similarity.</p></article></div>}
  </section>;
}
