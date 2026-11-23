const Parser = require('rss-parser');
const feeds = require('./feeds');

const parser = new Parser();
const REPORT_TREE_URL = 'https://api.github.com/repos/jacobdjwilson/awesome-annual-security-reports/git/trees/main?recursive=1';
const MAX_ITEMS_PER_FEED = 30;
const MAX_SUMMARY_LENGTH = 1600;

function plainText(value) {
  return String(value || '')
    .replace(/<script\b[^>]*>[\s\S]*?<\/script>/gi, ' ')
    .replace(/<style\b[^>]*>[\s\S]*?<\/style>/gi, ' ')
    .replace(/<[^>]*>/g, ' ')
    .replace(/&nbsp;|&#160;/gi, ' ')
    .replace(/&amp;/gi, '&')
    .replace(/&lt;/gi, '<')
    .replace(/&gt;/gi, '>')
    .replace(/&quot;/gi, '"')
    .replace(/&#39;|&apos;/gi, "'")
    .replace(/\s+/g, ' ')
    .trim();
}

function safeArticleUrl(value) {
  try {
    const url = new URL(value);
    return ['http:', 'https:'].includes(url.protocol) ? url.href : null;
  } catch {
    return null;
  }
}

function inferCategory(text) {
  const value = text.toLowerCase();
  if (/ransomware|extortion/.test(value)) return 'ransomware';
  if (/phishing|credential|business email compromise/.test(value)) return 'phishing';
  if (/vulnerability|cve-|zero.day|patch/.test(value)) return 'vulnerability';
  if (/malware|trojan|backdoor|botnet/.test(value)) return 'malware';
  if (/scanning|reconnaissance|exposed/.test(value)) return 'reconnaissance';
  return 'threat-intelligence';
}

function inferSeverity(text) {
  const value = text.toLowerCase();
  if (/actively exploited|zero.day|ransomware|critical vulnerability/.test(value)) return 'high';
  if (/vulnerability|malware|phishing|breach|exploit/.test(value)) return 'medium';
  return 'low';
}

function articleFromFeedItem(item, feed) {
  const title = plainText(item.title).slice(0, 300);
  const url = safeArticleUrl(item.link || item.guid);
  if (!title || !url) return null;

  const summary = plainText(item.contentSnippet || item.content || item.summary || item.description)
    .slice(0, MAX_SUMMARY_LENGTH);
  const published = new Date(item.isoDate || item.pubDate || Date.now());
  const text = `${title} ${summary}`;

  return {
    title,
    summary: summary || 'No summary was provided by the publisher.',
    category: inferCategory(text),
    severity: inferSeverity(text),
    publishedAt: Number.isNaN(published.getTime()) ? new Date() : published,
    sourceId: feed.name,
    sourceName: feed.name,
    sourceUrl: feed.url,
    source: { name: feed.name, url: feed.url, type: 'publisher', reliability: null },
    sourceAssessment: { verdict: 'needs-review' },
    canonicalUrl: url,
    tags: Array.isArray(item.categories) ? item.categories.map(plainText).filter(Boolean).slice(0, 12) : [],
    classification: 'needs-review',
    confidence: 55,
    isTrainingData: false,
    ingestionSource: 'ctidigest-rss',
    importedAt: new Date()
  };
}

async function fetchFeed(feed) {
  const response = await fetch(feed.url, {
    headers: { 'user-agent': 'lab7-mongodb/1.0 (RSS reader)' },
    signal: AbortSignal.timeout(12000)
  });
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  const xml = await response.text();
  const parsed = await parser.parseString(xml);
  return (parsed.items || [])
    .slice(0, MAX_ITEMS_PER_FEED)
    .map(item => articleFromFeedItem(item, feed))
    .filter(Boolean);
}

async function syncRssArticles(db) {
  await db.collection('sources').bulkWrite(
    feeds.map(feed => ({
      updateOne: {
        filter: { name: feed.name },
        update: {
          $set: { type: 'rss', url: feed.url, reliability: null },
          $setOnInsert: { name: feed.name }
        },
        upsert: true
      }
    })),
    { ordered: false }
  );
  const results = [];
  const queue = [...feeds];
  const workers = Array.from({ length: 6 }, async () => {
    while (queue.length) {
      const feed = queue.shift();
      try {
        const articles = await fetchFeed(feed);
        results.push({ feed: feed.name, articles });
      } catch (error) {
        results.push({ feed: feed.name, error: error.message });
      }
    }
  });
  await Promise.all(workers);

  const articles = [...new Map(
    results.flatMap(result => result.articles || []).map(article => [article.canonicalUrl, article])
  ).values()];
  let added = 0;
  if (articles.length) {
    const writes = await db.collection('articles').bulkWrite(
      articles.map(article => ({
        updateOne: {
          filter: { canonicalUrl: article.canonicalUrl },
          update: { $setOnInsert: article },
          upsert: true
        }
      })),
      { ordered: false }
    );
    added = writes.upsertedCount;
  }

  const failures = results.filter(result => result.error).map(({ feed, error }) => ({ feed, error }));
  if (!articles.length) {
    throw new Error(`No CTI RSS articles could be imported. ${failures.length} feeds failed.`);
  }
  return { feedsChecked: feeds.length, feedsSucceeded: results.length - failures.length, fetched: articles.length, added, failures };
}

async function syncAnnualReports(db) {
  const response = await fetch(REPORT_TREE_URL, {
    headers: { 'user-agent': 'lab7-mongodb/1.0' },
    signal: AbortSignal.timeout(12000)
  });
  if (!response.ok) throw new Error(`Annual report repository returned HTTP ${response.status}`);
  const tree = await response.json();
  if (!Array.isArray(tree.tree)) throw new Error('Annual report repository returned an invalid file listing.');
  const validRecords = tree.tree.flatMap(entry => {
    const match = entry.path.match(/^Annual Security Reports\/(20\d{2})\/(.+)$/);
    if (!match || entry.type !== 'blob') return [];
    const relativePath = `Annual Security Reports/${match[1]}/${match[2]}`;
    const encodedPath = relativePath.split('/').map(encodeURIComponent).join('/');
    const filename = match[2].split('/').pop().replace(/\.[^.]+$/, '');
    const title = plainText(filename.replace(/[-_]+/g, ' ')).slice(0, 300);
    const organization = plainText(filename.split(/[-_]/)[0]).slice(0, 160);
    return [{
      title,
      url: `https://github.com/jacobdjwilson/awesome-annual-security-reports/blob/main/${encodedPath}`,
      year: Number(match[1]),
      organization,
      category: 'Annual security report',
      summary: `${title} (${match[1]}) listed in the Awesome Annual Security Reports repository.`,
      discoveredAt: new Date(),
      isTrainingData: false,
      ingestionSource: 'awesome-annual-security-reports'
    }];
  });
  if (!validRecords.length) throw new Error('No annual report files were found in the repository.');
  let added = 0;
  if (validRecords.length) {
    const writes = await db.collection('annualReports').bulkWrite(
      validRecords.map(report => ({
        updateOne: {
          filter: { url: report.url },
          update: { $setOnInsert: report },
          upsert: true
        }
      })),
      { ordered: false }
    );
    added = writes.upsertedCount;
  }
  return { checked: validRecords.length, added };
}

async function syncIntelligence(db) {
  await Promise.all([
    db.collection('articles').createIndex(
      { canonicalUrl: 1 },
      { unique: true, partialFilterExpression: { canonicalUrl: { $type: 'string' } } }
    ),
    db.collection('annualReports').createIndex({ url: 1 }, { unique: true }),
    db.collection('sources').createIndex({ name: 1 }, { unique: true })
  ]);
  const [articles, reports] = await Promise.allSettled([
    syncRssArticles(db),
    syncAnnualReports(db)
  ]);
  if (articles.status === 'rejected' && reports.status === 'rejected') {
    throw new Error(`CTI RSS sync failed: ${articles.reason.message}; annual report sync failed: ${reports.reason.message}`);
  }
  return {
    articles: articles.status === 'fulfilled' ? articles.value : { error: articles.reason.message },
    reports: reports.status === 'fulfilled' ? reports.value : { error: reports.reason.message },
    checkedAt: new Date()
  };
}

module.exports = { feeds, syncIntelligence, syncRssArticles, syncAnnualReports };
