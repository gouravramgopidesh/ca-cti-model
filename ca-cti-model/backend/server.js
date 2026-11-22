require('dotenv').config();
const path = require('path');
const express = require('express');
const { MongoClient, ObjectId } = require('mongodb');
const { sources: sampleSources, buildArticles } = require('./data');
const { syncIntelligence, syncAnnualReports } = require('./intelligence');

const app = express();
app.use(express.json());
app.use(express.static(path.join(__dirname, '..', 'frontend')));

const client = new MongoClient(process.env.MONGODB_URI || 'mongodb://127.0.0.1:27017');
let db;
const classifications = ['confirmed-threat', 'benign', 'needs-review'];
const measuredCollections = ['articles', 'sources', 'indicators', 'annualReports'];
const DOCUMENT_LIMIT_BYTES = 16 * 1024 * 1024;

function validClassification(value) {
  return classifications.includes(value);
}

async function measureCollection(name) {
  const rows = await db.collection(name).aggregate([
    { $project: { bytes: { $bsonSize: '$$ROOT' } } },
    {
      $group: {
        _id: null,
        count: { $sum: 1 },
        averageBytes: { $avg: '$bytes' },
        maxBytes: { $max: '$bytes' },
        minBytes: { $min: '$bytes' }
      }
    }
  ]).toArray();
  return rows[0] || { count: 0, averageBytes: 0, maxBytes: 0, minBytes: 0 };
}

async function ensureIndexes() {
  await Promise.all([
    db.collection('articles').createIndex({ publishedAt: -1 }),
    db.collection('articles').createIndex({ severity: 1, category: 1 }),
    db.collection('articles').createIndex({ title: 'text', summary: 'text', tags: 'text' }),
    db.collection('articles').createIndex(
      { canonicalUrl: 1 },
      { unique: true, partialFilterExpression: { canonicalUrl: { $type: 'string' } } }
    ),
    db.collection('sources').createIndex({ name: 1 }, { unique: true }),
    db.collection('indicators').createIndex({ value: 1 }, { unique: true }),
    db.collection('annualReports').createIndex({ url: 1 }, { unique: true })
  ]);
}

async function migrateArticleAssessments() {
  const articleCollection = db.collection('articles');
  await articleCollection.updateMany(
    {
      $or: [
        { source: { $exists: false }, sourceName: { $exists: true } },
        { sourceAssessment: { $exists: false } },
        { classification: 'unreviewed' }
      ]
    },
    [{
      $set: {
        source: {
          $ifNull: [
            '$source',
            {
              name: '$sourceName',
              url: '$sourceUrl',
              type: 'publisher',
              reliability: null
            }
          ]
        },
        classification: {
          $cond: [
            { $in: ['$classification', classifications] },
            '$classification',
            'needs-review'
          ]
        },
        sourceAssessment: {
          $ifNull: [
            '$sourceAssessment',
            {
              verdict: {
                $cond: [
                  { $in: ['$classification', classifications] },
                  '$classification',
                  'needs-review'
                ]
              }
            }
          ]
        }
      }
    }]
  );
}

// AI chatbot routes stay on the Lab 7 origin; no second website needed.
const CHAT_INTERNAL = process.env.CHATBOT_INTERNAL_URL || 'http://chatbot:8000';
app.post('/api/chat', async (req, res) => {
  try {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 105000);
    try {
      const upstream = await fetch(`${CHAT_INTERNAL}/chat`, {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify(req.body || {}),
        signal: controller.signal
      });
      const payload = await upstream.json();
      return res.status(upstream.status).json(payload);
    } finally { clearTimeout(timeout); }
  } catch (err) {
    return res.status(503).json({ error: 'Chatbot unavailable. Start the chatbot and Ollama services.', detail: err.message });
  }
});
app.get('/api/chat/health', async (_, res) => {
  try { const r=await fetch(`${CHAT_INTERNAL}/health`,{signal:AbortSignal.timeout(4000)});res.status(r.status).json(await r.json()); }
  catch(err){res.status(503).json({ok:false,error:'Chatbot unavailable'});}
});
app.get('/api/chat/sessions/:id', async (req,res) => {
  if(!/^[a-zA-Z0-9_-]{1,64}$/.test(req.params.id))return res.status(400).json({error:'Invalid session'});
  try { const r=await fetch(`${CHAT_INTERNAL}/api/sessions/${req.params.id}`,{signal:AbortSignal.timeout(5000)});res.status(r.status).json(await r.json()); }
  catch(err){res.status(503).json({error:'Chat memory unavailable'});}
});

app.get('/api/health', (_, res) => {
  res.json({ ok: true, database: Boolean(db), mode: db ? 'mongo' : 'demo' });
});

app.get('/api/articles', async (req, res, next) => {
  try {
    const query = typeof req.query.q === 'string' ? req.query.q.trim() : '';
    const filter = {};
    for (const key of ['severity', 'category', 'classification']) {
      if (typeof req.query[key] === 'string' && req.query[key]) filter[key] = req.query[key];
    }
    if (query) filter.$text = { $search: query };

    const requestedLimit = Number(req.query.limit);
    const limit = Math.min(100, Math.max(1, Number.isFinite(requestedLimit) && requestedLimit ? requestedLimit : 30));
    const articles = db.collection('articles');
    const [items, total, priorityTotal] = await Promise.all([
      articles.find(filter).sort({ publishedAt: -1 }).limit(limit).toArray(),
      articles.countDocuments(filter),
      articles.countDocuments({ severity: { $in: ['critical', 'high'] } })
    ]);
    res.json({ items, total, priorityTotal });
  } catch (error) {
    next(error);
  }
});

app.get('/api/sources', async (_, res, next) => {
  try {
    res.json(await db.collection('sources').find().sort({ reliability: -1, name: 1 }).toArray());
  } catch (error) {
    next(error);
  }
});

app.get('/api/indicators', async (req, res, next) => {
  try {
    const query = typeof req.query.q === 'string' ? req.query.q.trim() : '';
    const filter = query
      ? { value: { $regex: query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), $options: 'i' } }
      : {};
    res.json(await db.collection('indicators').find(filter).limit(100).sort({ firstSeen: -1 }).toArray());
  } catch (error) {
    next(error);
  }
});

app.patch('/api/articles/:id/classification', async (req, res, next) => {
  try {
    if (!ObjectId.isValid(req.params.id) || !validClassification(req.body?.classification)) {
      return res.status(400).json({ error: 'Invalid article ID or classification' });
    }
    const result = await db.collection('articles').findOneAndUpdate(
      { _id: new ObjectId(req.params.id) },
      {
        $set: {
          classification: req.body.classification,
          'sourceAssessment.verdict': req.body.classification,
          reviewedAt: new Date(),
          'sourceAssessment.reviewedAt': new Date()
        }
      },
      { returnDocument: 'after' }
    );
    if (!result) return res.status(404).json({ error: 'Article not found' });
    res.json(result);
  } catch (error) {
    next(error);
  }
});

app.get('/api/lab/schema', async (_, res, next) => {
  try {
    const entries = await Promise.all(measuredCollections.map(async name => [name, await measureCollection(name)]));
    const collections = Object.fromEntries(entries);
    const maxBytes = Math.max(0, ...Object.values(collections).map(item => item.maxBytes));
    res.json({
      collections,
      articles: collections.articles,
      sources: collections.sources.count,
      indicators: collections.indicators.count,
      annualReports: collections.annualReports.count,
      limitBytes: DOCUMENT_LIMIT_BYTES,
      largestDocumentBytes: maxBytes,
      percentOfLimit: +(maxBytes / DOCUMENT_LIMIT_BYTES * 100).toFixed(4),
      relationships: [
        {
          name: 'Article → source',
          kind: 'reference plus embedded snapshot',
          reason: 'The source catalog is canonical; each article also embeds the small publisher snapshot used to render it without a lookup.',
          alternative: 'Remove the snapshot and fetch the publisher record by sourceId at read time, reducing duplication but adding a lookup.'
        },
        {
          name: 'Article → threat assessment',
          kind: 'embedded',
          reason: 'The analyst verdict is bounded and consumed with the article, so it lives in sourceAssessment on that article.',
          alternative: 'A separate assessment collection could provide a central history, but displaying the verdict would require another query or lookup.'
        },
        {
          name: 'Indicators → article/source provenance',
          kind: 'reference',
          reason: 'An indicator can recur in many reports and is independently searchable and updateable.',
          alternative: 'Embed a bounded indicator snapshot on each article; this helps article detail reads but makes cross-report IOC search and consistency harder.'
        },
        {
          name: 'Annual reports → publisher',
          kind: 'publisher snapshot',
          reason: 'The source list is externally maintained and reports are stored with their publisher name and URL.',
          alternative: 'A separate publisher collection avoids repeating publisher metadata but requires lookups.'
        }
      ]
    });
  } catch (error) {
    next(error);
  }
});

app.get('/api/lab/cache', async (_, res, next) => {
  try {
    const status = await db.admin().command({ serverStatus: 1 });
    const cache = status.wiredTiger?.cache || {};
    const cacheBytes = cache['bytes currently in the cache'] || 0;
    const maxBytes = cache['maximum bytes configured'] || 0;
    res.json({
      available: true,
      cacheBytes,
      maxBytes,
      cacheUsePct: maxBytes ? +(cacheBytes / maxBytes * 100).toFixed(2) : 0,
      pagesRead: cache['pages read into cache'] || 0,
      pagesRequested: cache['pages requested from the cache'] || 0,
      generatedAt: new Date()
    });
  } catch (error) {
    if (error.codeName === 'Unauthorized') {
      return res.json({ available: false, message: 'MongoDB user needs serverStatus privilege.' });
    }
    next(error);
  }
});

app.post('/api/intelligence/sync', async (_, res, next) => {
  try {
    res.json(await syncIntelligence(db));
  } catch (error) {
    res.status(502).json({ error: `Intelligence sync failed: ${error.message}` });
  }
});

app.post('/api/reports/discover', async (_, res, next) => {
  try {
    res.json({ reports: await syncAnnualReports(db), checkedAt: new Date() });
  } catch (error) {
    res.status(502).json({ error: `Report discovery failed: ${error.message}` });
  }
});

app.get('/api/reports', async (_, res, next) => {
  try {
    res.json(await db.collection('annualReports').find().sort({ year: -1 }).limit(50).toArray());
  } catch (error) {
    next(error);
  }
});

app.use((error, _, res, __) => {
  console.error(error);
  res.status(500).json({ error: error.message || 'Server error' });
});

(async () => {
  try {
    await client.connect();
    db = client.db(process.env.DB_NAME || 'lab7-mongodb');
    if (!await db.collection('articles').countDocuments()) {
      await db.collection('sources').insertMany(sampleSources);
      await db.collection('articles').insertMany(buildArticles());
      await db.collection('indicators').insertOne({
        value: 'training-login.example.invalid',
        kind: 'domain',
        confidence: 70,
        category: 'phishing',
        firstSeen: new Date(),
        sourceName: 'Training dataset',
        isTrainingData: true
      });
    }
    await migrateArticleAssessments();
    await ensureIndexes();
    const port = Number(process.env.PORT) || 3000;
    app.listen(port, () => console.log(`lab7-mongodb listening at http://localhost:${port}`));
    syncIntelligence(db)
      .then(result => console.log(`Background sync added ${result.articles.added || 0} articles and ${result.reports.added || 0} reports.`))
      .catch(error => console.warn(`Background live sync failed: ${error.message}`));
  } catch (error) {
    console.error('Cannot connect to MongoDB:', error.message);
    process.exit(1);
  }
})();
