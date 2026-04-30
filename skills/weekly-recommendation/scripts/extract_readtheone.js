(function() {
  // Robust emoji/symbol cleaner: removes common emojis and decorative symbols
  function cleanEmoji(str) {
    if (!str) return '';
    return str
      .replace(/[\u{1F300}-\u{1F9FF}]/gu, '')   // emoticons, symbols, flags
      .replace(/[\u{2600}-\u{26FF}]/gu, '')     // misc symbols
      .replace(/[\u{2700}-\u{27BF}]/gu, '')     // dingbats
      .replace(/[🔗⚡🔥]/gu, '')                // explicit known symbols
      .trim();
  }

  function getCleanText(el, extraRemove) {
    if (!el) return '';
    const textEl = el.querySelector('.project-name-text');
    const text = textEl ? textEl.textContent : el.textContent;
    let cleaned = cleanEmoji(text);
    if (extraRemove) {
      cleaned = cleaned.replace(new RegExp('[' + extraRemove + ']', 'g'), '');
    }
    return cleaned.replace(/\n/g, ' ').replace(/\s+/g, ' ').trim();
  }

  const rows = document.querySelectorAll('.ranking-row:not(.ranking-header)');
  const data = [];
  rows.forEach(row => {
    const rankEl = row.querySelector('.col-rank');
    let rank = rankEl ? cleanEmoji(rankEl.textContent) : '';
    rank = rank.replace(/\s+/g, ' ').trim();
    if (!rank && rankEl && /[🥇🥈🥉]/.test(rankEl.textContent)) {
      rank = String(data.length + 1);
    }

    // Name: prefer .project-name-text inside .col-name, fallback to <a>, then raw .col-name
    const nameCol = row.querySelector('.col-name');
    const nameTextEl = nameCol ? nameCol.querySelector('.project-name-text') : null;
    const nameAEl = nameCol ? nameCol.querySelector('a') : null;
    let name = '';
    if (nameTextEl) {
      name = nameTextEl.textContent;
    } else if (nameAEl) {
      name = nameAEl.textContent;
    } else if (nameCol) {
      name = nameCol.textContent;
    }
    name = cleanEmoji(name).replace(/\n/g, ' ').replace(/\s+/g, ' ').trim();

    // Tags: extract type keywords below the name (e.g., AI Application, ML, LLM)
    let tags = [];
    if (nameCol) {
      // Try common tag container selectors
      const tagContainer = nameCol.querySelector('.project-inline-tags, .inline-tags, .tags, .project-tags');
      if (tagContainer) {
        tagContainer.querySelectorAll('.tag, .badge, .pill, span').forEach(tagEl => {
          const t = cleanEmoji(tagEl.textContent).replace(/\n/g, ' ').replace(/\s+/g, ' ').trim();
          if (t && t !== name) tags.push(t);
        });
      } else {
        // Fallback: scan all direct children of .col-name except the name element
        const nameText = name.toLowerCase();
        Array.from(nameCol.children).forEach(child => {
          if (child === nameTextEl || child === nameAEl) return;
          const t = cleanEmoji(child.textContent).replace(/\n/g, ' ').replace(/\s+/g, ' ').trim();
          if (t && t !== name && t.toLowerCase() !== nameText) {
            // Split by common delimiters in case multiple tags are in one element
            t.split(/[,\/|·•]/).forEach(part => {
              const p = part.trim();
              if (p && p.toLowerCase() !== nameText) tags.push(p);
            });
          }
        });
      }
    }
    // Deduplicate tags
    tags = [...new Set(tags)];

    const score = cleanEmoji(row.querySelector('.col-score') ? row.querySelector('.col-score').textContent : '').replace(/\s+/g, ' ').trim();
    const reason = cleanEmoji(row.querySelector('.col-reason') ? row.querySelector('.col-reason').textContent : '').replace(/\n/g, ' ').replace(/\s+/g, ' ').trim();

    // Source: prefer .project-name-text to avoid mixing in tags
    const sourceCol = row.querySelector('.col-source');
    const sourceTextEl = sourceCol ? sourceCol.querySelector('.project-name-text') : null;
    const source = cleanEmoji(sourceTextEl ? sourceTextEl.textContent : (sourceCol ? sourceCol.textContent : '')).replace(/\s+/g, ' ').trim();

    // Track: same safeguard
    const trackCol = row.querySelector('.col-track');
    const trackTextEl = trackCol ? trackCol.querySelector('.project-name-text') : null;
    const track = cleanEmoji(trackTextEl ? trackTextEl.textContent : (trackCol ? trackCol.textContent : '')).replace(/\n/g, ' ').replace(/\s+/g, ' ').trim();

    if (name && name !== '项目名称') {
      data.push({ rank, name, score, reason, source, track, tags });
    }
  });
  return JSON.stringify(data);
})();
