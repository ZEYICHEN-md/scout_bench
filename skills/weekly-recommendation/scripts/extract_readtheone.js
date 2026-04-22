(function() {
  const rows = document.querySelectorAll('.ranking-row:not(.ranking-header)');
  const data = [];
  rows.forEach(row => {
    const rankEl = row.querySelector('.col-rank');
    let rank = rankEl ? rankEl.textContent.replace(/[🥇🥈🥉🔗⚡\n\s]/g, '').trim() : '';
    if (!rank && rankEl && /[🥇🥈🥉]/.test(rankEl.textContent)) {
      rank = String(data.length + 1);
    }
    const nameEl = row.querySelector('.col-name a');
    const name = nameEl ? nameEl.textContent.replace(/[🔗\n\s]/g, '').trim() : (row.querySelector('.col-name') ? row.querySelector('.col-name').textContent.replace(/[🔗\n\s]/g, '').trim() : '');
    const score = row.querySelector('.col-score') ? row.querySelector('.col-score').textContent.replace(/[🔥🔗⚡\n\s]/g, '').trim() : '';
    const reason = row.querySelector('.col-reason') ? row.querySelector('.col-reason').textContent.replace(/\n/g, ' ').trim() : '';
    const source = row.querySelector('.col-source') ? row.querySelector('.col-source').textContent.replace(/[🔗⚡\n\s]/g, '').trim() : '';
    const track = row.querySelector('.col-track') ? row.querySelector('.col-track').textContent.replace(/\n/g, '').trim() : '';
    if (name && name !== '项目名称') {
      data.push({ rank, name, score, reason, source, track });
    }
  });
  return JSON.stringify(data);
})();
