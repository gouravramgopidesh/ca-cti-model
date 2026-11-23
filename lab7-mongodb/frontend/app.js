const $ = selector => document.querySelector(selector);
const esc = value => String(value ?? '').replace(/[&<>"']/g, character => ({
  '&': '&amp;',
  '<': '&lt;',
  '>': '&gt;',
  '"': '&quot;',
  "'": '&#39;'
}[character]));
const pretty = bytes => bytes >= 1048576
  ? `${(bytes / 1048576).toFixed(2)} MB`
  : bytes >= 1024 ? `${(bytes / 1024).toFixed(1)} KB` : `${bytes} B`;
let toastTimer;

async function api(endpoint, options) {
  const response = await fetch(`/api${endpoint}`, options);
  const body = await response.json();
  if (!response.ok) throw new Error(body.error || response.statusText);
  return body;
}

function ago(value) {
  const seconds = Math.max(0, (Date.now() - new Date(value)) / 1000);
  if (seconds < 3600) return `${Math.max(1, Math.floor(seconds / 60))}m ago`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
  return `${Math.floor(seconds / 86400)}d ago`;
}

function renderArticles(items) {
  $('#feedList').innerHTML = items.length ? items.map(article => {
    const isLive = article.ingestionSource === 'ctidigest-rss';
    const title = isLive && article.canonicalUrl
      ? `<a href="${esc(article.canonicalUrl)}" target="_blank" rel="noopener noreferrer">${esc(article.title)}</a>`
      : esc(article.title);
    const verdict = article.classification || 'needs-review';
    const verdictText = verdict === 'confirmed-threat'
      ? 'Threat confirmed'
      : verdict === 'benign' ? 'Marked benign' : 'Needs review';
    return `<article class="article">
      <div class="article-top">
        <span class="severity ${esc(article.severity)}">${esc(article.severity)}</span>
        <span class="category-tag">${esc((article.category || 'intelligence').replaceAll('-', ' '))}</span>
        <span class="${isLive ? 'live-pill' : 'training-pill'}">${isLive ? 'LIVE RSS' : 'SAMPLE'}</span>
        <time>${ago(article.publishedAt)}</time>
      </div>
      <h3>${title}</h3>
      <p>${esc(article.summary)}</p>
      <div class="article-meta">
        <span>◉ ${esc(article.sourceName || 'Unknown source')}</span>
        <span>·</span>
        <span>CONF ${esc(article.confidence ?? '—')}%</span>
        <span>·</span>
        <span>${esc(article.mitreTechnique || article.ingestionSource || 'CTI')}</span>
        <button class="classify ${esc(verdict)}" data-id="${esc(article._id)}" data-class="${esc(verdict)}" aria-label="Change analyst threat verdict: ${esc(verdictText)}">${esc(verdictText)} ▾</button>
      </div>
    </article>`;
  }).join('') : '<div class="loading">No intelligence matches those filters.</div>';
  $('#resultCount').textContent = `${items.length} RECORDS SHOWN`;
}

async function loadArticles() {
  const params = new URLSearchParams();
  const query = $('#searchInput').value.trim();
  if (query) params.set('q', query);
  if ($('#severityFilter').value) params.set('severity', $('#severityFilter').value);
  if ($('#categoryFilter').value) params.set('category', $('#categoryFilter').value);
  try {
    const result = await api(`/articles?${params}`);
    renderArticles(result.items);
    $('#statArticles').textContent = result.total.toLocaleString();
    $('#statPriority').textContent = String(result.priorityTotal).padStart(2, '0');
  } catch (error) {
    $('#feedList').innerHTML = `<div class="loading">${esc(error.message)} · Start MongoDB, then run npm run seed.</div>`;
  }
}

async function loadSources() {
  try {
    const sources = (await api('/sources')).sort((left, right) =>
      Number(right.type === 'rss') - Number(left.type === 'rss')
    );
    $('#sourceList').innerHTML = sources.slice(0, 5).map((source, index) => `
      <div class="source-row">
        <span class="source-icon">${esc(source.name.slice(0, 1) || ['C', 'H', 'S', 'N', 'A'][index])}</span>
        <span class="source-name">${esc(source.name)}<span class="source-type">${esc(source.type)} intelligence</span></span>
        <span class="score">${source.reliability == null ? 'RSS' : `${esc(source.reliability)}%`}</span>
      </div>`).join('');
    $('#statSources').textContent = String(sources.length).padStart(2, '0');
  } catch (error) {
    $('#sourceList').innerHTML = `<div class="loading">${esc(error.message)}</div>`;
  }
}

async function loadIndicators() {
  try {
    const params = new URLSearchParams();
    const query = $('#iocSearch').value.trim();
    if (query) params.set('q', query);
    const indicators = await api(`/indicators?${params}`);
    $('#statIocs').textContent = String(indicators.length).padStart(2, '0');
    $('#iocRows').innerHTML = indicators.length ? indicators.map(indicator => `
      <tr>
        <td>${esc(indicator.value)} ${indicator.isTrainingData ? '<span class="training-pill">SAMPLE</span>' : ''}</td>
        <td><span class="type-pill">${esc(indicator.kind)}</span></td>
        <td><span class="confidence">${esc(indicator.confidence)}%</span></td>
        <td>${esc(indicator.category)}</td>
        <td>${new Date(indicator.firstSeen).toLocaleDateString()}</td>
      </tr>`).join('') : '<tr><td colspan="5" class="loading">No indicators found.</td></tr>';
  } catch (error) {
    $('#iocRows').innerHTML = `<tr><td colspan="5">${esc(error.message)}</td></tr>`;
  }
}

async function loadLab() {
  try {
    const result = await api('/lab/schema');
    $('#avgSize').textContent = pretty(Math.round(result.articles.averageBytes));
    $('#maxSize').textContent = pretty(result.largestDocumentBytes);
    $('#limitUse').textContent = `${result.percentOfLimit}%`;
    $('#avgSize').title = `${result.articles.count} article docs · ${result.articles.count ? pretty(result.articles.minBytes) : '—'} min`;
    $('#lab').dataset.schema = JSON.stringify(result);
  } catch (error) {
    $('#avgSize').textContent = 'Unavailable';
    $('#avgSize').title = error.message;
  }
}

function reportCard(report) {
  return `<article class="report-card">
    <small>${esc(report.organization)} · ${esc(report.year)} ${report.isTrainingData ? '· SAMPLE' : ''}</small>
    <h3>${esc(report.title)}</h3>
    <p>${esc(report.summary)}</p>
    <a href="${esc(report.url)}" target="_blank" rel="noopener noreferrer">Open report ↗</a>
  </article>`;
}

async function loadReports() {
  try {
    const reports = await api('/reports');
    $('#reportCards').innerHTML = reports.slice(0, 6).map(reportCard).join('')
      || '<p class="muted">No reports yet. Sync to check the public annual report index.</p>';
  } catch (error) {
    $('#reportCards').innerHTML = `<p class="muted">${esc(error.message)}</p>`;
  }
}

function showToast(message) {
  const toast = $('#toast');
  toast.textContent = message;
  toast.classList.add('show');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toast.classList.remove('show'), 3000);
}

document.addEventListener('click', async event => {
  const button = event.target.closest('.classify');
  if (!button) return;
  const options = ['confirmed-threat', 'benign', 'needs-review'];
  const next = options[(options.indexOf(button.dataset.class) + 1) % options.length];
  try {
    await api(`/articles/${encodeURIComponent(button.dataset.id)}/classification`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ classification: next })
    });
    showToast(`Analyst verdict updated: ${next}`);
    await loadArticles();
  } catch (error) {
    showToast(error.message);
  }
});

let searchTimer;
$('#searchInput').addEventListener('input', () => {
  clearTimeout(searchTimer);
  searchTimer = setTimeout(loadArticles, 250);
});
$('#severityFilter').addEventListener('change', loadArticles);
$('#categoryFilter').addEventListener('change', loadArticles);
$('#iocSearch').addEventListener('input', () => {
  clearTimeout(searchTimer);
  searchTimer = setTimeout(loadIndicators, 250);
});

$('#refreshBtn').addEventListener('click', () => {
  loadArticles();
  loadSources();
  loadIndicators();
  loadLab();
  loadReports();
  showToast('Dashboard refreshed');
});

$('#discoverBtn').textContent = '↻ Sync intelligence';
$('.live').innerHTML = '<i></i> RSS SYNC AVAILABLE';
document.querySelector('.source-panel h2').textContent = 'RSS sources';
$('#statSources').nextElementSibling.textContent = 'CTI Digest-listed feeds';
$('.feed-footer span:last-child').textContent = 'Live RSS records and labeled training samples';
document.querySelector('footer span:last-child').textContent = 'Live RSS articles · sample records labeled';
if (!$('#categoryFilter').querySelector('option[value="threat-intelligence"]')) {
  const option = document.createElement('option');
  option.value = 'threat-intelligence';
  option.textContent = 'Threat intelligence';
  $('#categoryFilter').append(option);
}
$('#discoverBtn').addEventListener('click', async () => {
  const button = $('#discoverBtn');
  button.disabled = true;
  $('#discoverStatus').textContent = 'Checking CTI RSS feeds and the annual report index…';
  try {
    const result = await api('/intelligence/sync', { method: 'POST' });
    const articleResult = result.articles;
    const reportResult = result.reports;
    const articleStatus = articleResult.error
      ? `RSS sync failed: ${articleResult.error}`
      : `${articleResult.added} new RSS articles from ${articleResult.feedsSucceeded}/${articleResult.feedsChecked} feeds`;
    const reportStatus = reportResult.error
      ? `annual reports failed: ${reportResult.error}`
      : `${reportResult.added} new annual reports`;
    const failures = articleResult.failures?.length
      ? ` · ${articleResult.failures.length} feeds unavailable` : '';
    $('#discoverStatus').textContent = `${articleStatus} · ${reportStatus}${failures} · ${new Date(result.checkedAt).toLocaleTimeString()}`;
    await Promise.all([loadArticles(), loadSources(), loadReports()]);
  } catch (error) {
    $('#discoverStatus').textContent = error.message;
  } finally {
    button.disabled = false;
  }
});

$('#cacheBtn').addEventListener('click', async () => {
  $('#modalBackdrop').classList.add('open');
  $('#cacheDetails').textContent = 'Loading…';
  try {
    const result = await api('/lab/cache');
    $('#cacheDetails').innerHTML = result.available
      ? `Cache currently used: <b>${pretty(result.cacheBytes)}</b> (${result.cacheUsePct}% of configured capacity)<br>
         Maximum configured: <b>${pretty(result.maxBytes)}</b><br>
         Pages read into cache (cumulative): <b>${result.pagesRead.toLocaleString()}</b><br>
         Pages requested from cache (cumulative): <b>${result.pagesRequested.toLocaleString()}</b><br><br>
         These server-wide figures are not collection-specific. Run <code>npm run working-set</code> to compare the test collection with cache capacity and sample counter deltas every 10 seconds.`
      : esc(result.message);
  } catch (error) {
    $('#cacheDetails').textContent = error.message;
  }
});

$('#modalClose').addEventListener('click', () => $('#modalBackdrop').classList.remove('open'));
$('#modalBackdrop').addEventListener('click', event => {
  if (event.target.id === 'modalBackdrop') event.currentTarget.classList.remove('open');
});
$('#themeBtn').addEventListener('click', () => document.body.classList.toggle('light'));

$('#today').textContent = new Date().toLocaleDateString(undefined, {
  month: 'short',
  day: '2-digit',
  year: 'numeric'
}).toUpperCase();

loadArticles();
loadSources();
loadIndicators();
loadLab();
loadReports();
