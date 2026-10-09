export const B = import.meta.env.VITE_API_URL || "/api"
async function j(r) { if (!r.ok) throw new Error((await r.json().catch(() => ({}))).detail || "Request failed (" + r.status + ")"); return r.json() }
const J = { "Content-Type": "application/json" }
export const api = {
  analyze: (text, files) => { const f = new FormData(); f.append("text", text); files.forEach(x => f.append("files", x)); return fetch(B + "/analyze", { method: "POST", body: f }).then(j) },
  startJob: (text, files, onUp) => new Promise((res, rej) => { const x = new XMLHttpRequest(); x.open('POST', B + '/jobs'); x.upload.onprogress = e => e.lengthComputable && onUp?.(e.loaded / e.total)
    x.onload = () => { try { const d = JSON.parse(x.responseText); x.status < 300 ? res(d) : rej(new Error(d.detail || 'Upload failed')) } catch { rej(new Error('Upload failed')) } }
    x.onerror = () => rej(new Error('Network error')); const f = new FormData(); f.append('text', text); files.forEach(y => f.append('files', y)); x.send(f) }),
  job: id => fetch(B + '/jobs/' + id).then(j),
  get: id => fetch(B + "/analysis/" + id).then(j),
  review: (id, body) => fetch(B + "/analysis/" + id + "/review", { method: "POST", headers: J, body: JSON.stringify(body) }).then(j),
  history: (v = "") => fetch(B + "/history?verdict=" + v).then(j), del: id => fetch(B + "/analysis/" + id, { method: "DELETE" }).then(j), research: () => fetch(B + "/research/results").then(j),
  dataset: () => fetch(B + "/dataset/statistics").then(j), cases: () => fetch(B + "/cases").then(j)
}
