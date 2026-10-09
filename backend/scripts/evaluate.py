"""Run real experiments. Usage:
  python scripts/evaluate.py --manifest data/manifest.csv            # runs models, caches data/scores.jsonl
  python scripts/evaluate.py --scores data/scores.jsonl [--faith]    # reuse cached model outputs
manifest.csv columns: id,path,text,label(REAL|FAKE),source,manip_type[,split]   (path may be empty for text-only rows)
Writes data/results.json, dataset.json, cases.json, fusion.json (learned fusion used by the API)."""
import argparse, csv, json, hashlib, sys, collections
from pathlib import Path
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, roc_auc_score, average_precision_score
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
MODS = ["text", "image", "audio", "video", "cross_modal"]

def feats(sc, mods):  # value (0 if missing) + presence flag per modality
    return [x for m in mods for x in ((sc[m], 1) if sc.get(m) is not None else (0, 0))]
def split_of(r): return r.get("split") or ["train", "train", "train", "val", "test"][int(hashlib.md5(r["id"].encode()).hexdigest(), 16) % 5]
def fit(rows, mods): return LogisticRegression(C=1.0, max_iter=1000).fit([feats(r["scores"], mods) for r in rows], [r["y"] for r in rows])
def mean_p(sc, mods): v = [sc[m] for m in mods if sc.get(m) is not None]; return float(np.mean(v)) if v else 0.5
def metrics(y, p):
    yh = [int(x >= .5) for x in p]; pr, rc, f1, _ = precision_recall_fscore_support(y, yh, average="binary", zero_division=0)
    both = len(set(y)) == 2
    return {"accuracy": round(accuracy_score(y, yh), 4), "precision": round(pr, 4), "recall": round(rc, 4), "f1": round(f1, 4), "n": len(y),
            "roc_auc": round(roc_auc_score(y, p), 4) if both else None, "pr_auc": round(average_precision_score(y, p), 4) if both else None}
def ece(y, p, bins=10):
    y, p = np.array(y), np.array(p); e = 0
    for i in range(bins):
        m = (p >= i / bins) & (p < (i + 1) / bins + (i == bins - 1))
        if m.any(): e += m.mean() * abs(y[m].mean() - p[m].mean())
    return round(float(e), 4)
def row(name, m): return {"name": name, **m}

def collect(manifest, out):
    import main
    rows = []
    for r in csv.DictReader(open(manifest)):
        files = [{"name": Path(r["path"]).name, "data": open(r["path"], "rb").read()}] if r.get("path") else []
        try: res = main.run(r.get("text", ""), files)
        except Exception as e: print("skip", r["id"], e); continue
        rows.append({**r, "scores": res["modalities"], "evidence": res["evidence"], "detail": {k: {x: v for x, v in d.items() if x in ("highlights", "engine")} for k, d in res["detail"].items()}})
    out.write_text("\n".join(json.dumps(x) for x in rows)); return rows

def main_():
    ap = argparse.ArgumentParser(); ap.add_argument("--manifest"); ap.add_argument("--scores"); ap.add_argument("--out", default="data"); ap.add_argument("--faith", action="store_true")
    a = ap.parse_args(); out = Path(a.out); out.mkdir(exist_ok=True)
    rows = [json.loads(l) for l in open(a.scores)] if a.scores else collect(a.manifest, out / "scores.jsonl")
    for r in rows: r["y"] = int(r["label"].upper() == "FAKE"); r["split"] = split_of(r)
    tr, va, te = [[r for r in rows if r["split"] == s] for s in ("train", "val", "test")]
    assert len(tr) > 5 and te, "need train and test rows"
    present = [m for m in MODS if any(r["scores"].get(m) is not None for r in rows)]
    lr = fit(tr, present); pf = lambda rs, mods=present, model=lr: model.predict_proba([feats(r["scores"], mods) for r in rs])[:, 1]
    yt = [r["y"] for r in te]; res = {"available": True, "n_test": len(te), "modalities": present}
    # Exp 1: baselines vs multimodal
    res["baselines"] = [row(m.title() + " only", metrics([r["y"] for r in sub], [r["scores"][m] for r in sub])) for m in present if (sub := [r for r in te if r["scores"].get(m) is not None])]
    res["baselines"].append(row("Multimodal (learned fusion)", metrics(yt, pf(te))))
    # Exp 2: fusion strategies
    res["fusion"] = [row("Mean (decision-level)", metrics(yt, [mean_p(r["scores"], present) for r in te])),
                     row("Max (decision-level)", metrics(yt, [max([r["scores"][m] for m in present if r["scores"].get(m) is not None] or [.5]) for r in te])),
                     row("Learned LR (stacking)", metrics(yt, pf(te)))]
    # Exp 4: ablation (retrain without each modality)
    res["ablation"] = [row("Full model", metrics(yt, pf(te)))]
    for m in present:
        sub = [x for x in present if x != m]
        if sub: mm = fit(tr, sub); res["ablation"].append(row(f"Remove {m}", metrics(yt, pf(te, sub, mm))))
    # Exp 3: leave-one-source-out generalization
    res["generalization"] = []
    for s in sorted({r["source"] for r in rows}):
        a_, b_ = [r for r in rows if r["source"] != s], [r for r in rows if r["source"] == s]
        if len(a_) > 5 and len({r["y"] for r in a_}) == 2 and b_: res["generalization"].append(row(f"Held-out source: {s}", metrics([r["y"] for r in b_], pf(b_, present, fit(a_, present)))))
    # calibration + abstention band tuned on validation (maximise accuracy on confident cases with >=70% coverage)
    pv, yv = pf(va or tr), [r["y"] for r in (va or tr)]; best = (0, .5, .5)
    for w in np.arange(0, .31, .02):
        keep = [i for i, p in enumerate(pv) if abs(p - .5) >= w]
        if len(keep) >= .7 * len(pv):
            acc = np.mean([(pv[i] >= .5) == yv[i] for i in keep])
            if acc > best[0] + 1e-9: best = (acc, w, len(keep) / len(pv))
    band = float(best[1]); pt = pf(te)
    pred = ["UNCERTAIN" if abs(p - .5) < band else ("FAKE" if p >= .5 else "REAL") for p in pt]
    res["abstain_band"] = band; res["ece"] = ece(yt, pt)
    res["confusion"] = {"labels": ["REAL", "FAKE", "UNCERTAIN"], "matrix": [[sum(1 for r, p in zip(te, pred) if r["y"] == y and p == c) for c in ["REAL", "FAKE", "UNCERTAIN"]] for y in (0, 1)]}
    res["confusion"]["rows"] = ["REAL", "FAKE"]
    # Exp 6: explanation faithfulness (text): does deleting flagged phrases lower the text score?
    if a.faith:
        import models; drops = []
        for r in te:
            hl = (r["detail"].get("text") or {}).get("highlights") or []
            if hl and r.get("text"):
                t = r["text"]
                for h in sorted(hl, key=lambda h: -h["start"]): t = t[:h["start"]] + t[h["end"]:]
                try: drops.append(r["scores"]["text"] - models.text_analysis(t)["score"])
                except Exception: pass
        if drops: res["explanation"] = {"n": len(drops), "mean_score_drop": round(float(np.mean(drops)), 4), "frac_positive": round(float(np.mean([d > 0 for d in drops])), 4)}
    (out / "results.json").write_text(json.dumps(res, indent=1))
    c = collections.Counter
    (out / "dataset.json").write_text(json.dumps({"available": True, "total": len(rows), "classes": c(r["label"].upper() for r in rows), "sources": c(r["source"] for r in rows),
        "manipulation_types": c(r.get("manip_type", "") for r in rows), "modalities": {m: sum(1 for r in rows if r["scores"].get(m) is not None) for m in present},
        "splits": c(r["split"] for r in rows), "provenance": "see manifest.csv (source column); verify licences before redistribution"}, indent=1))
    wrong = [(abs(p - r["y"]), r, pr_) for r, p, pr_ in zip(te, pt, pred) if pr_ != ("FAKE" if r["y"] else "REAL")]; wrong.sort(key=lambda x: -x[0])
    (out / "cases.json").write_text(json.dumps([{"id": r["id"], "expected": "FAKE" if r["y"] else "REAL", "predicted": pr_, "source": r["source"], "manip_type": r.get("manip_type", ""),
        "scores": r["scores"], "reason": f"Model scores {r['scores']}; fused P(fake)={1 - abs(d - r['y']) if False else (d if not r['y'] else 1 - d):.2f}. Evidence: " + "; ".join(e["description"] for e in r["evidence"][:2])} for d, r, pr_ in wrong[:30]], indent=1))
    lrm = {"features": present, "coef": lr.coef_[0].tolist(), "intercept": float(lr.intercept_[0]), "band": band}
    (out / "fusion.json").write_text(json.dumps(lrm)); print(json.dumps(res["fusion"], indent=1)); print("cases:", min(len(wrong), 30))

if __name__ == "__main__": main_()
