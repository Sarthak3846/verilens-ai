import { Component, useEffect, useState } from 'react'
import { Routes, Route, NavLink, Link, useParams, useNavigate, useLocation } from 'react-router-dom'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'
import { api, B } from './api'

const NAV = [['/verify', 'Verify'], ['/playground', 'Playground'], ['/history', 'History'], ['/compare', 'Compare'], ['/research', 'Research'], ['/dataset', 'Dataset'], ['/cases', 'Cases'], ['/methodology', 'Method'], ['/about', 'About']]
const COL = { REAL: '#1f6f45', FAKE: '#b42323', UNCERTAIN: '#a24a00' }  // all >=5.4:1 on cream and white
async function runJob(text, files, onStage, onUp) {
  const { job_id } = await api.startJob(text, files, onUp)
  for (;;) { const j = await api.job(job_id); onStage(j.stage); if (j.status === 'done') return j.analysis_id; if (j.status === 'error') throw new Error(j.error); await new Promise(r => setTimeout(r, 600)) }
}
const pct = x => `${(x * 100).toFixed(1)}%`

function useLoad(fn, deps = []) {
  const [s, set] = useState({ loading: true })
  const run = () => { set({ loading: true }); fn().then(data => set({ data }), e => set({ error: e.message })) }
  useEffect(run, deps)
  return [s, run]
}
const Status = ({ s, retry }) => s.loading ? <div role="status" aria-live="polite" className="py-8 space-y-3 animate-pulse motion-reduce:animate-none"><span className="sr-only">Loading…</span>{[60, 90, 75].map(w => <div key={w} className="h-8 bg-sand" style={{ width: `${w}%` }} />)}</div> : s.error ? <div role="alert" className="card border-red-700 my-6">{s.error} <button className="btn ml-3" onClick={retry}>Retry</button></div> : null
class Boundary extends Component {
  state = { e: null }
  static getDerivedStateFromError(e) { return { e } }
  render() { return this.state.e ? <div role="alert" className="card my-8"><h1 className="h1 text-4xl">Something went wrong</h1><p className="my-3">{String(this.state.e.message || this.state.e)}</p><button className="btn" onClick={() => this.setState({ e: null })}>Try again</button></div> : this.props.children }
}
const NotFound = () => <div className="py-16"><h1 className="h1 text-6xl">Page not found</h1><Link to="/" className="btn btn-o mt-6">Back to home</Link></div>

const TITLES = Object.fromEntries(NAV.map(([p, l]) => [p, l]))
function Layout({ children }) {
  const { pathname } = useLocation()
  useEffect(() => {
    window.scrollTo(0, 0)
    document.title = `${pathname.startsWith('/analysis') ? 'Analysis report' : TITLES[pathname] || 'Home'} · VeriLens AI`
    document.getElementById('main')?.focus({ preventScroll: true })
  }, [pathname])
  return <div className="max-w-6xl mx-auto px-4 sm:px-5 pb-16">
    <a href="#main" className="sr-only focus:not-sr-only focus:absolute focus:z-50 focus:bg-brand focus:p-3 focus:border-2 focus:border-ink">Skip to content</a>
    <header className="flex items-center justify-between py-3 gap-3 flex-wrap">
      <Link to="/" className="font-pixel text-2xl min-h-[44px] inline-flex items-center gap-1"><span aria-hidden="true" className="text-brand">▞</span> VERILENS AI</Link>
      <nav id="site-nav" aria-label="Main" className="flex flex-wrap items-center gap-x-5 gap-y-0 w-full lg:w-auto order-last lg:order-none text-base">
        {NAV.map(([p, l]) => <NavLink key={p} to={p} className={({ isActive }) => `min-h-[44px] inline-flex items-center px-1 hover:underline ${isActive ? 'font-bold underline decoration-4 decoration-brand underline-offset-8' : ''}`}>{l}</NavLink>)}
      </nav>
      <Link to="/verify" className="btn">Verify content</Link>
    </header>
    <main id="main" tabIndex={-1} className="outline-none fade">{children}</main>
    <footer className="mt-16 pt-6 border-t-2 border-ink text-sm text-ink/80 space-y-1"><p>VeriLens AI · CSET 346 multimodal NLP project.</p></footer></div>
}

function Landing() {
  const steps = ['Input', 'Modality detection', 'Per-modality analysis', 'Multimodal fusion', 'REAL / FAKE / UNCERTAIN', 'Evidence + report']
  return <>
    <section className="py-10"><h1 className="h1 text-5xl sm:text-6xl md:text-8xl max-w-3xl">We verify bold claims across text, image, audio and video.</h1>
      <p className="mt-6 max-w-xl text-ink/80">Multimodal NLP for deepfake detection. Every verdict comes with confidence, evidence and an honest UNCERTAIN when modalities disagree.</p>
      <div className="mt-8 flex gap-4 flex-wrap"><Link to="/verify" className="btn btn-o">Verify content</Link><Link to="/research" className="btn">Research</Link></div>
      <div aria-hidden="true" className="font-pixel text-5xl sm:text-7xl md:text-9xl mt-10 select-none overflow-hidden">VERILENS</div></section>
    <section className="bg-ink text-cream p-8 grid md:grid-cols-6 gap-4 border-l-8 border-brand">{steps.map((s, i) => <div key={s}><div className="font-pixel text-brand text-3xl">0{i + 1}</div><div className="font-display text-xl uppercase">{s}</div></div>)}</section></>
}

function Verify() {
  const [text, setText] = useState(''), [files, setFiles] = useState([]), [busy, setBusy] = useState(false), [err, setErr] = useState(''), [stage, setStage] = useState(''), [up, setUp] = useState(1)
  const nav = useNavigate()
  const add = l => setFiles(f => [...f, ...Array.from(l)])
  const kinds = { Text: !!text.trim(), Image: files.some(f => f.type.startsWith('image')), Audio: files.some(f => f.type.startsWith('audio')), Video: files.some(f => f.type.startsWith('video')) }
  const go = async () => {
    setErr(''); setBusy(true); setUp(0); setStage('Uploading')
    try { nav(`/analysis/${await runJob(text, files, setStage, setUp)}`) } catch (e) { setErr(e.message) } finally { setBusy(false) }
  }
  return <div className="py-8"><h1 className="h1 text-5xl">Verify digital content</h1>
    <div role="group" aria-label="File drop zone" onDragOver={e => e.preventDefault()} onDrop={e => { e.preventDefault(); add(e.dataTransfer.files) }} className="mt-6 border-2 border-dashed border-ink p-10 text-center bg-white">
      <p className="font-display text-2xl">Drop files here</p><p className="text-sm text-ink/75">JPG PNG WEBP · MP3 WAV M4A · MP4 MOV WEBM</p>
      <label className="btn mt-4 cursor-pointer">Browse<input type="file" multiple hidden accept="image/*,audio/*,video/*" onChange={e => add(e.target.files)} /></label></div>
    <div className="grid md:grid-cols-2 gap-5 mt-5">
      <div><label htmlFor="caption" className="font-display text-xl">Text / caption</label><textarea id="caption" value={text} onChange={e => setText(e.target.value)} rows={6} className="w-full border-2 border-ink p-3 bg-white" placeholder="Paste text, caption or transcript…" /></div>
      <div><p className="font-display text-xl">Detected modalities</p>
        <div className="flex gap-3 flex-wrap my-2">{Object.entries(kinds).map(([k, v]) => <span key={k} className={`px-3 py-1 border-2 border-ink ${v ? 'bg-brand' : 'bg-sand'}`}>{k} <span aria-hidden="true">{v ? '✓' : '✗'}</span><span className="sr-only">{v ? 'detected' : 'not detected'}</span></span>)}</div>
        {files.map((f, i) => <div key={i} className="flex items-center gap-3 mb-2 text-sm">{f.type.startsWith('image') && <img alt={`Preview of ${f.name}`} src={URL.createObjectURL(f)} className="h-12" />}<span className="truncate flex-1">{f.name}</span><button aria-label={`Remove ${f.name}`} className="border-2 border-ink min-w-[44px] min-h-[44px]" onClick={() => setFiles(files.filter((_, j) => j !== i))}>✕</button></div>)}</div></div>
    {err && <div role="alert" className="card border-red-700 mt-4">{err}</div>}
    {busy && <p role="status" aria-live="polite" className="mt-4 font-display text-xl">{up < 1 ? `Uploading ${Math.round(up * 100)}%` : `${stage}…`}</p>}
    {busy && <div role="progressbar" aria-label="Upload progress" aria-valuenow={Math.round(up * 100)} aria-valuemin="0" aria-valuemax="100" className="h-3 border-2 border-ink mt-2 max-w-md"><div className="h-full bg-brand transition-all" style={{ width: `${up * 100}%` }} /></div>}
    <button disabled={busy || (!text.trim() && !files.length)} onClick={go} className="btn btn-o mt-5 disabled:bg-sand disabled:text-ink/75 disabled:cursor-not-allowed">{err ? 'Retry analysis' : 'Analyze content'}</button></div>
}

function Analysis() {
  const { id } = useParams(); const nav = useNavigate()
  const [s, retry] = useLoad(() => api.get(id), [id])
  const [rv, setRv] = useState({ verdict: 'REAL', notes: '' }), [saved, setSaved] = useState(null)
  if (!s.data) return <Status s={s} retry={retry} />
  const r = s.data, t = r.detail.text, img = r.detail.image, review = saved || r.review
  return <div className="py-8 space-y-5">
    <div className="flex justify-between items-end flex-wrap gap-3"><div className="min-w-0"><p className="text-sm">Analysis {r.id} · {(r.processing_ms / 1000).toFixed(1)} s</p>
      <h1 className="h1 text-6xl sm:text-8xl" style={{ color: COL[r.prediction] }}>{r.prediction}</h1><p className="font-display text-3xl">Confidence {pct(r.confidence)}</p></div>
      <div className="flex gap-2 noprint"><a className="btn" href={`${B}/analysis/${id}/report.pdf`}>PDF</a><button className="btn" onClick={() => { const u = URL.createObjectURL(new Blob([JSON.stringify(r, null, 2)], { type: 'application/json' })); Object.assign(document.createElement('a'), { href: u, download: `verilens-${id}.json` }).click() }}>JSON</button><button className="btn" onClick={() => api.del(id).then(() => nav('/history'))}>Delete</button></div></div>
    <div className="card"><h2 className="font-display text-2xl">Why this verdict?</h2><p>{r.explanation.replace(/\s*This is an assisted assessment, not proof\.?/, '')}</p></div>
    <div className="grid md:grid-cols-2 gap-5">
      <div className="card"><h2 className="font-display text-2xl">Why not the other classes?</h2>
        <div role="img" aria-label={`Class probabilities: ${Object.entries(r.probabilities).map(([k, v]) => `${k} ${pct(v)}`).join(", ")}`} className="h-44"><ResponsiveContainer><BarChart data={Object.entries(r.probabilities).map(([k, v]) => ({ k, v }))}><XAxis dataKey="k" /><YAxis domain={[0, 1]} /><Tooltip formatter={pct} /><Bar dataKey="v" fill="#ff7a1a" /></BarChart></ResponsiveContainer></div></div>
      <div className="card"><h2 className="font-display text-2xl">Modality scores (P fake)</h2>
        {Object.entries(r.modalities).map(([k, v]) => <div key={k} className="my-2"><div className="flex justify-between"><span className="uppercase">{k}</span><span>{v == null ? 'not scored' : pct(v)}</span></div>
          <div role="progressbar" aria-valuenow={Math.round((v || 0) * 100)} aria-valuemin="0" aria-valuemax="100" aria-label={`${k} P(fake)`} className="h-3 border border-ink"><div className="h-full bg-brand" style={{ width: `${(v || 0) * 100}%` }} /></div>{r.detail[k]?.note && <p className="text-xs text-ink/75">{r.detail[k].note}</p>}</div>)}
        <p className="text-xs mt-3">Cross-modal truth meter requires a CLIP-style adapter (not configured).</p></div></div>
    <div className="card"><h2 className="font-display text-2xl">Evidence</h2>
      {r.evidence.length ? r.evidence.map((e, i) => <p key={i}><b className="uppercase">{e.severity}</b> · {e.type.replace('_', ' ')} — {e.description}</p>) : <p>No manipulation indicators found.</p>}
      {t && r.text && <p className="mt-3 p-3 bg-cream border border-ink">{(() => { let i = 0; const o = []; [...t.highlights].sort((x, y) => x.start - y.start).forEach((h, k) => { if (h.start < i) return; o.push(r.text.slice(i, h.start), <mark key={k} className="bg-brand/50">{r.text.slice(h.start, h.end)}</mark>); i = h.end }); o.push(r.text.slice(i)); return o })()}</p>}
      {t && <><p className="mt-3 text-sm">Entities: {t.entities.join(', ') || '—'}</p><p className="text-sm">Flagged phrases: {t.highlights.map((h, i) => <mark key={i} className="bg-brand/40 mr-1 px-1">{h.text}</mark>)}{!t.highlights.length && 'none'}</p></>}</div>
    {r.contributions && <div className="card"><h2 className="font-display text-2xl">Evidence contribution</h2>{Object.entries(r.contributions).map(([k, v]) => <div key={k} className="my-1"><div className="flex justify-between"><span className="uppercase">{k}</span><span>{pct(v)}</span></div><div className="h-3 border border-ink"><div className="h-full bg-ink" style={{ width: `${v * 100}%` }} /></div></div>)}<p className="text-xs mt-2">Share of total deviation from 50% across scored modalities.</p></div>}
    {r.consistency && <div className="card"><h2 className="font-display text-2xl">Cross-modal truth meter</h2>
      {[['text_image', 'Text ↔ Image'], ['text_audio', 'Text ↔ Audio'], ['image_audio', 'Image ↔ Audio']].map(([k, l]) => r.consistency[k] != null && <div key={k} className="my-2"><div className="flex justify-between"><span>{l}</span><span>{pct(r.consistency[k])}</span></div><div className="h-3 border border-ink"><div className="h-full" style={{ width: `${r.consistency[k] * 100}%`, background: r.consistency[k] < .5 ? COL.FAKE : COL.REAL }} /></div></div>)}</div>}
    {['video', 'audio'].map(k => r.detail[k]?.timeline && <div key={k} className="card"><h2 className="font-display text-2xl">{k} timeline (P fake per {k === 'video' ? 'frame' : 'window'})</h2>
      <div role="img" aria-label={`${k} timeline: ${r.detail[k].timeline.length} segments, ${r.detail[k].timeline.filter(x => x.score > .7).length} suspicious`} className="flex items-end gap-1 h-32">{r.detail[k].timeline.map((x, i) => <div key={i} title={`${x.t}s: ${pct(x.score)}`} className="flex-1 border border-ink" style={{ height: `${Math.max(4, x.score * 100)}%`, background: x.score > .7 ? COL.FAKE : x.score > .5 ? COL.UNCERTAIN : COL.REAL }} />)}</div>
      <p className="text-xs mt-1">Hover bars for timestamps. Red = suspicious segments.</p></div>)}
    {r.detail.audio?.transcript && <div className="card"><h2 className="font-display text-2xl">Transcript</h2><p>{r.detail.audio.transcript}</p></div>}
    <div className="card"><h2 className="font-display text-2xl">Evidence graph</h2>{(() => { const m = Object.entries(r.modalities).filter(([, v]) => v != null); return <svg role="img" aria-label={`Evidence graph: ${m.map(([k, v]) => `${k} ${pct(v)}`).join(", ")} lead to ${r.prediction}`} viewBox={`0 0 600 ${Math.max(120, m.length * 60 + 20)}`} className="w-full max-w-xl">
      {m.map(([k, v], i) => <g key={k}><rect x="10" y={10 + i * 60} width="140" height="40" fill="#fff" stroke="#2b2b2b" strokeWidth="2" /><text x="20" y={35 + i * 60} fontSize="14">{k} {pct(v)}</text>
        <line x1="150" y1={30 + i * 60} x2="450" y2={Math.max(120, m.length * 60 + 20) / 2} stroke={v > .5 ? COL.FAKE : COL.REAL} strokeWidth={1 + v * 6} /></g>)}
      <rect x="450" y={Math.max(120, m.length * 60 + 20) / 2 - 22} width="140" height="44" fill={COL[r.prediction]} /><text x="470" y={Math.max(120, m.length * 60 + 20) / 2 + 6} fill="#fff" fontSize="16">{r.prediction}</text></svg> })()}</div>
    {r.notes?.length > 0 && <div className="card text-sm">{r.notes.map((n, i) => <p key={i}>{n}</p>)}</div>}
    {img && <div className="card"><h2 className="font-display text-2xl">Image evidence (ELA compression heatmap)</h2><img alt="Error-level-analysis heatmap highlighting compression differences in the uploaded image" src={img.heatmap} className="max-h-96 max-w-full" /></div>}
    <div className="card noprint"><h2 className="font-display text-2xl">Human review</h2>
      {review ? <p>Reviewer verdict: <b>{review.verdict}</b> — {review.notes}</p> :
        <div className="flex gap-3 flex-wrap"><select aria-label="Reviewer verdict" value={rv.verdict} onChange={e => setRv({ ...rv, verdict: e.target.value })} className="border-2 border-ink p-2 min-h-[44px]">{Object.keys(COL).map(v => <option key={v}>{v}</option>)}</select>
          <input aria-label="Reviewer notes" className="border-2 border-ink p-2 flex-1 min-h-[44px]" placeholder="Reviewer notes" value={rv.notes} onChange={e => setRv({ ...rv, notes: e.target.value })} /><button className="btn" onClick={() => api.review(id, rv).then(setSaved)}>Save review</button></div>}</div>
    <details className="card text-sm"><summary className="cursor-pointer font-display text-xl">Models used</summary>
      <ul className="mt-2 space-y-1">{Object.entries((() => { try { return JSON.parse(r.model_version) } catch { return { version: r.model_version } } })()).map(([k, v]) => <li key={k}><b className="uppercase">{k}</b>: {v}</li>)}</ul></details>
    <p className="text-xs">{new Date(r.timestamp * 1000).toLocaleString()}</p></div>
}

function History() {
  const [v, setV] = useState('')
  const [s, retry] = useLoad(() => api.history(v), [v])
  if (!s.data) return <Status s={s} retry={retry} />
  return <div className="py-8"><h1 className="h1 text-5xl mb-4">History</h1><select aria-label="Filter by verdict" value={v} onChange={e => setV(e.target.value)} className="border-2 border-ink p-2 mb-4 min-h-[44px]"><option value="">All verdicts</option>{Object.keys(COL).map(k => <option key={k}>{k}</option>)}</select>{s.data.length === 0 && <p>No analyses yet.</p>}
    {s.data.map(h => <Link key={h.id} to={`/analysis/${h.id}`} className="card flex justify-between mb-2 hover:bg-sand"><span>{h.id} · {new Date(h.timestamp * 1000).toLocaleString()}</span><b style={{ color: COL[h.prediction] }}>{h.prediction} {pct(h.confidence)}</b></Link>)}</div>
}

function Diff({ a, b }) {
  const ks = [...new Set([...Object.keys(a.modalities), ...Object.keys(b.modalities)])], th = 'pr-4 text-left'
  return <div className="card mt-5 overflow-x-auto"><h2 className="font-display text-2xl">Differences</h2>
    <p>Verdict: {a.prediction} → {b.prediction} {a.prediction === b.prediction ? '(same)' : '(changed)'}</p>
    <table className="text-sm mt-2"><thead><tr><th scope="col" className={th}>Modality</th><th scope="col" className={th}>A</th><th scope="col" className={th}>B</th><th scope="col" className="text-left">Change</th></tr></thead>
      <tbody>{ks.map(k => { const x = a.modalities[k], y = b.modalities[k]; return <tr key={k}><th scope="row" className={th + ' font-normal'}>{k}</th><td className="pr-4">{x == null ? '—' : pct(x)}</td><td className="pr-4">{y == null ? '—' : pct(y)}</td><td>{x == null || y == null ? '—' : `${y - x >= 0 ? '+' : ''}${((y - x) * 100).toFixed(1)} pts`}</td></tr> })}</tbody></table>
    <p className="text-sm mt-2">Evidence items: {a.evidence.length} vs {b.evidence.length}. Confidence: {pct(a.confidence)} vs {pct(b.confidence)}.</p></div>
}

function Compare() {
  const [a, setA] = useState(''), [b, setB] = useState(''), [s, retry] = useLoad(api.history), [out, setOut] = useState(null)
  const go = () => Promise.all([api.get(a), api.get(b)]).then(setOut).catch(e => setOut({ error: e.message }))
  return <div className="py-8"><h1 className="h1 text-5xl mb-4">Compare</h1><Status s={s} retry={retry} />
    <div className="flex gap-3 flex-wrap">{[[a, setA], [b, setB]].map(([v, f], i) => <select key={i} aria-label={`Analysis ${i + 1}`} value={v} onChange={e => f(e.target.value)} className="border-2 border-ink p-2 min-h-[44px]"><option value="">Select analysis</option>{s.data?.map(h => <option key={h.id} value={h.id}>{h.id} — {h.prediction}</option>)}</select>)}
      <button className="btn btn-o" disabled={!a || !b} onClick={go}>Compare</button></div>
    {out?.error && <p>{out.error}</p>}
    {Array.isArray(out) && <><Diff a={out[0]} b={out[1]} /><div className="grid md:grid-cols-2 gap-5 mt-5">{out.map(r => <div key={r.id} className="card"><b style={{ color: COL[r.prediction] }}>{r.prediction} {pct(r.confidence)}</b>{Object.entries(r.modalities).map(([k, v]) => <p key={k}>{k}: {v == null ? '—' : pct(v)}</p>)}<p className="text-sm mt-2">{r.explanation}</p></div>)}</div></>}</div>
}

const PRESETS = [
  { t: 'Plain news-style sentence', text: 'The city council approved the 2025 budget on Tuesday after a three-hour public meeting.', note: 'Hypothesis: low text suspicion.' },
  { t: 'Sensational, unsupported claim', text: 'BREAKING!!! Leaked secret: scientists EXPOSED, share before it is banned! The Moon is now sovereign territory of India.', note: 'Hypothesis: high text suspicion.' },
  { t: 'Hinglish claim', text: 'Pradhan Mantri ne announce kiya ki chaand ab India ka hissa hai, 100% sach hai!', note: 'Hypothesis: flagged as unsupported (code-mixed input).' },
  { t: 'Mismatched caption + image', text: 'A crowded beach on a sunny day.', image: true, note: 'Hypothesis: cross-modal inconsistency (the image is a plain dark-blue graphic).' }]
const blueprint = () => new Promise(res => { const c = document.createElement('canvas'); c.width = c.height = 256; const x = c.getContext('2d'); x.fillStyle = '#1d3557'; x.fillRect(0, 0, 256, 256); x.fillStyle = '#fff'; x.font = '28px sans-serif'; x.fillText('BLUEPRINT', 60, 135); c.toBlob(b => res(new File([b], 'blueprint.png', { type: 'image/png' }))) })
function Playground() {
  const [busy, setBusy] = useState(''), [err, setErr] = useState(''), nav = useNavigate()
  const run = async p => { setErr(''); setBusy(p.t); try { nav(`/analysis/${await runJob(p.text, p.image ? [await blueprint()] : [], () => {}, () => {})}`) } catch (e) { setErr(e.message) } finally { setBusy('') } }
  return <div className="py-8"><h1 className="h1 text-5xl">Sanity playground</h1>
    <p className="max-w-2xl my-3">Controlled inputs for checking that the system behaves sensibly. Presets only supply the input — every verdict is computed live by the real models. A result that contradicts the hypothesis is a finding worth recording, not a bug to hide.</p>
    {err && <div role="alert" className="card border-red-700 my-3">{err}</div>}
    <div className="grid md:grid-cols-2 gap-4">{PRESETS.map(p => <div key={p.t} className="card"><h2 className="font-display text-2xl">{p.t}</h2><p className="text-sm my-2">“{p.text}”{p.image && ' + generated image'}</p><p className="text-sm text-ink/80 mb-3">{p.note}</p><button className="btn btn-o" disabled={!!busy} onClick={() => run(p)}>{busy === p.t ? 'Running…' : 'Run through pipeline'}</button></div>)}</div>
    <p className="text-sm mt-4">Want genuine vs manipulated <em>media</em> pairs? Upload your own licensed samples on the Verify page.</p></div>
}
const Empty = ({ d }) => <div className="card">{d?.message || 'No data available.'}</div>
function Research() {
  const [s, retry] = useLoad(api.research)
  if (!s.data) return <Status s={s} retry={retry} />
  const d = s.data
  if (d.available === false) return <div className="py-8"><h1 className="h1 text-5xl mb-4">Research dashboard</h1><Empty d={d} /></div>
  const sets = [['baselines', 'Baseline vs multimodal'], ['fusion', 'Fusion strategies'], ['ablation', 'Modality ablation'], ['generalization', 'Generalization']]
  return <div className="py-8 space-y-6"><h1 className="h1 text-5xl">Research dashboard</h1>
    {sets.map(([k, t]) => d[k]?.length > 0 && <div key={k} className="card"><h2 className="font-display text-2xl">{t}</h2><div role="img" aria-label={`${t} chart; exact values in the metrics table below`} className="h-60"><ResponsiveContainer><BarChart data={d[k]}><XAxis dataKey="name" /><YAxis /><Tooltip /><Bar dataKey="accuracy" fill="#2b2b2b" /><Bar dataKey="f1" fill="#ff7a1a" /></BarChart></ResponsiveContainer></div></div>)}
    {d.confusion?.matrix && <div className="card"><h2 className="font-display text-2xl">Confusion matrix (test split, abstain band ±{d.abstain_band?.toFixed(2)})</h2><table><thead><tr><td />{d.confusion.labels.map(l => <th scope="col" key={l} className="p-2">{l}</th>)}</tr></thead><tbody>{d.confusion.matrix.map((row, i) => <tr key={i}><th scope="row" className="pr-3">{d.confusion.rows[i]}</th>{row.map((c, j) => <td key={j} className="border-2 border-ink p-3 text-center">{c}</td>)}</tr>)}</tbody></table><p className="text-sm mt-2">ECE {d.ece} · n={d.n_test}</p></div>}
    {d.explanation && <div className="card"><h2 className="font-display text-2xl">Explanation faithfulness</h2><p>Removing flagged phrases lowered the text score in {pct(d.explanation.frac_positive)} of {d.explanation.n} cases (mean drop {d.explanation.mean_score_drop}).</p></div>}
    {d.baselines && <div className="card overflow-x-auto"><h2 className="font-display text-2xl">Metrics</h2><table className="text-sm"><thead><tr>{['Model', 'Acc', 'P', 'R', 'F1', 'ROC-AUC', 'PR-AUC'].map(h => <th scope="col" key={h} className="pr-4 text-left">{h}</th>)}</tr></thead><tbody>{[...d.baselines, ...(d.fusion || [])].map((r, i) => <tr key={i}><td className="pr-4">{r.name}</td>{[r.accuracy, r.precision, r.recall, r.f1, r.roc_auc, r.pr_auc].map((x, j) => <td key={j} className="pr-4">{x ?? '—'}</td>)}</tr>)}</tbody></table></div>}</div>
}
function Dataset() {
  const [s, retry] = useLoad(api.dataset)
  if (!s.data) return <Status s={s} retry={retry} />
  return <div className="py-8"><h1 className="h1 text-5xl mb-4">Dataset explorer</h1>{s.data.available === false ? <Empty d={s.data} /> : <div className="space-y-5"><p className="font-display text-3xl">Total samples: {s.data.total}</p><div className="grid md:grid-cols-2 gap-5">{['classes', 'modalities', 'sources', 'splits', 'manipulation_types'].map(k => s.data[k] && <div key={k} className="card"><h2 className="font-display text-2xl capitalize">{k.replace('_', ' ')}</h2><div role="img" aria-label={`${k.replace("_", " ")}: ${Object.entries(s.data[k]).map(([n, c]) => `${n} ${c}`).join(", ")}`} className="h-44"><ResponsiveContainer><BarChart data={Object.entries(s.data[k]).map(([name, n]) => ({ name, n }))}><XAxis dataKey="name" /><YAxis /><Tooltip /><Bar dataKey="n" fill="#ff7a1a" /></BarChart></ResponsiveContainer></div></div>)}</div><p className="text-sm">{s.data.provenance}</p></div>}</div>
}
function Cases() {
  const [s, retry] = useLoad(api.cases)
  if (!s.data) return <Status s={s} retry={retry} />
  return <div className="py-8"><h1 className="h1 text-5xl mb-4">Difficult cases</h1>
    {s.data.length === 0 && <Empty d={{ message: 'No cases loaded. Add real analyzed cases to backend/data/cases.json.' }} />}
    <div className="grid md:grid-cols-3 gap-4">{s.data.map(c => <div key={c.id} className="card"><b>CASE #{String(c.id).padStart(2, '0')}</b><p>Expected: {c.expected}</p><p>Predicted: {c.predicted}</p>{c.source && <p className="text-xs">{c.source} · {c.manip_type}</p>}<p className="text-sm">{c.reason}</p></div>)}</div></div>
}
const Page = ({ title, children }) => <div className="py-8 max-w-3xl space-y-3"><h1 className="h1 text-5xl">{title}</h1>{children}</div>
const Methodology = () => <Page title="Methodology"><p>Pipeline: input → validation → modality detection → per-modality engines → decision-level (late) fusion → three-way verdict → evidence → report.</p><p><b>Text:</b> cue-phrase, entity and claim extraction (baseline heuristics). <b>Image:</b> Error Level Analysis heatmap. <b>Audio/Video:</b> adapter slots for Whisper / wav2vec2 / frame models. <b>Fusion:</b> mean fake-probability; UNCERTAIN mass grows with modality disagreement and missing evidence.</p><p>Current engines are baselines, not trained detectors. Replace them in backend/main.py and write real experiment outputs to backend/data/.</p></Page>
const About = () => <Page title="About"><p>VeriLens AI — CSET 346 multimodal NLP project on explainable deepfake detection.</p><p>Privacy: text, images and transcripts may be sent to Google Gemini for analysis. Uploads are not stored by this app. Uploads are processed in memory and not stored; only analysis metadata is kept. Do not upload private individuals' media without permission.</p></Page>

export default function App() {
  return <Layout><Boundary><Routes><Route path="/" element={<Landing />} /><Route path="/verify" element={<Verify />} /><Route path="/playground" element={<Playground />} /><Route path="/analysis/:id" element={<Analysis />} /><Route path="/history" element={<History />} /><Route path="/compare" element={<Compare />} /><Route path="/research" element={<Research />} /><Route path="/dataset" element={<Dataset />} /><Route path="/cases" element={<Cases />} /><Route path="/methodology" element={<Methodology />} /><Route path="/about" element={<About />} /><Route path="*" element={<NotFound />} /></Routes></Boundary></Layout>
}