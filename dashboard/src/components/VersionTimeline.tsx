// src/components/VersionTimeline.tsx
import { versions } from "@/data/versions";

export function VersionTimeline() {
  return (
    <div className="version-strip">
      {versions.map((v) => (
        <div key={v.id} className={`version-card${v.isCurrent ? " current" : ""}`}>
          <div>
            <span className="version-id">{v.id}</span>
            <span className="version-date">{v.date}</span>
          </div>
          <div className="version-summary">{v.summary || "—"}</div>
          <ul className="version-changes">
            {v.changes.slice(0, 4).map((c, i) => (
              <li key={i}>{c.length > 60 ? c.slice(0, 60) + "…" : c}</li>
            ))}
          </ul>
        </div>
      ))}
    </div>
  );
}
