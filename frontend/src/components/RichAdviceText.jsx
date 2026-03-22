import React from "react";

function parseInline(text) {
  if (!text) return null;
  const nodes = [];
  let key = 0;
  const re = /\*\*([^*]+)\*\*/g;
  let last = 0;
  let m;
  while ((m = re.exec(text)) !== null) {
    if (m.index > last) {
      nodes.push(<span key={key++}>{text.slice(last, m.index)}</span>);
    }
    nodes.push(<strong key={key++}>{m[1]}</strong>);
    last = re.lastIndex;
  }
  if (last < text.length) {
    nodes.push(<span key={key++}>{text.slice(last)}</span>);
  }
  return nodes.length ? nodes : text;
}

function isBulletLine(line) {
  const t = line.trim();
  return /^[\*\-•]\s+/.test(t) || /^\d+\.\s/.test(t);
}

function stripBullet(line) {
  const t = line.trim();
  const star = t.match(/^[\*\-•]\s+(.+)$/);
  if (star) return star[1];
  const num = t.match(/^\d+\.\s+(.+)$/);
  if (num) return num[1];
  return t;
}

export default function RichAdviceText({ text, className = "" }) {
  if (!text || typeof text !== "string") return null;

  const lines = text.split(/\r?\n/);
  const blocks = [];
  let i = 0;
  let blockKey = 0;

  while (i < lines.length) {
    const line = lines[i];
    const trimmed = line.trim();

    if (!trimmed) {
      i += 1;
      continue;
    }

    if (isBulletLine(line)) {
      const items = [];
      while (i < lines.length && isBulletLine(lines[i])) {
        items.push(stripBullet(lines[i]));
        i += 1;
      }
      blocks.push(
        <ul key={blockKey++} className="finsight-rich-list">
          {items.map((item, idx) => (
            <li key={idx}>{parseInline(item)}</li>
          ))}
        </ul>
      );
      continue;
    }

    const para = [];
    while (i < lines.length) {
      const L = lines[i].trim();
      if (!L) break;
      if (isBulletLine(lines[i])) break;
      para.push(L);
      i += 1;
    }
    if (para.length) {
      blocks.push(
        <p key={blockKey++} className="finsight-rich-p">
          {para.map((pl, idx) => (
            <React.Fragment key={idx}>
              {idx > 0 && <br />}
              {parseInline(pl)}
            </React.Fragment>
          ))}
        </p>
      );
    }
  }

  return <div className={`finsight-rich-text ${className}`.trim()}>{blocks}</div>;
}
