// Lab 7.2: create a 100,000-document working set, sample random reads, and sync new reports.
require('dotenv').config();
const { MongoClient } = require('mongodb');
const fs = require('node:fs');
const path = require('node:path');
const { syncIntelligence } = require('./intelligence');

const DOCUMENT_COUNT = Number(process.env.WORKING_SET_SIZE || 100000);
const BATCH_SIZE = 1000;
const READS_PER_SAMPLE = 1000;
const SAMPLE_INTERVAL_MS = 10000;
const REPORT_SYNC_INTERVAL_MS = Number(process.env.REPORT_SYNC_INTERVAL_MS || 600000);
const RUN_ONCE = process.argv.includes('--once');
const payload = 'x'.repeat(1900);
const evidenceDir = path.join(__dirname, '..', 'evidence');
fs.mkdirSync(evidenceDir, { recursive: true });
const evidenceFile = path.join(evidenceDir, `lab72_${Date.now()}.jsonl`);
function record(data) { fs.appendFileSync(evidenceFile, JSON.stringify(data) + '\n'); }

if (!Number.isSafeInteger(DOCUMENT_COUNT) || DOCUMENT_COUNT < 1) {
  throw new Error('WORKING_SET_SIZE must be a positive integer.');
}
if (!Number.isSafeInteger(REPORT_SYNC_INTERVAL_MS) || REPORT_SYNC_INTERVAL_MS < SAMPLE_INTERVAL_MS) {
  throw new Error('REPORT_SYNC_INTERVAL_MS must be at least 10000 milliseconds.');
}

async function syncReports(db) {
  try {
    const result = await syncIntelligence(db);
    record({type: "report-sync", at: new Date(), result});
    const articlesAdded = result.articles.added || 0;
    const reportsAdded = result.reports.added || 0;
    console.log(`${new Date().toISOString()} report sync: ${articlesAdded} new CTI articles, ${reportsAdded} new annual reports.`);
    if (result.articles.failures?.length) {
      console.warn(`RSS sync warning: ${result.articles.failures.length} of ${result.articles.feedsChecked} feeds failed.`);
    }
    if (result.articles.error) console.warn(`RSS sync failed: ${result.articles.error}`);
    if (result.reports.error) console.warn(`Annual report sync failed: ${result.reports.error}`);
  } catch (error) {
    record({type: "report-sync-error", at: new Date(), error: error.message});
    console.warn(`Report sync failed: ${error.message}`);
  }
}

(async () => {
  const client = new MongoClient(process.env.MONGODB_URI || 'mongodb://127.0.0.1:27017');
  try {
    await client.connect();
    const db = client.db(process.env.DB_NAME || 'lab7-mongodb');
    const collection = db.collection('workingSet');

    console.log(`Evidence: ${evidenceFile}`);
    console.log(`Recreating only the workingSet collection with ${DOCUMENT_COUNT.toLocaleString()} documents.`);
    const reportRows = await db.collection('annualReports').find({isTrainingData: {$ne: true}}, {projection: {title:1, year:1, url:1}}).toArray();
    await collection.deleteMany({});
    for (let base = 0; base < DOCUMENT_COUNT; base += BATCH_SIZE) {
      const count = Math.min(BATCH_SIZE, DOCUMENT_COUNT - base);
      const documents = Array.from({ length: count }, (_, offset) => ({
        seq: base + offset,
        createdAt: new Date(),
        reportId: reportRows.length ? reportRows[(base + offset) % reportRows.length]._id : null,
        payload: `sample-${base + offset}-${payload}`
      }));
      await collection.insertMany(documents, { ordered: false });
    }
    await collection.createIndex({ seq: 1 });

    const [sizeResult, count] = await Promise.all([
      collection.aggregate([
        { $project: { bytes: { $bsonSize: '$$ROOT' } } },
        { $group: { _id: null, totalBytes: { $sum: '$bytes' }, maxBytes: { $max: '$bytes' } } }
      ]).toArray(),
      collection.countDocuments()
    ]);
    const datasetBytes = sizeResult[0]?.totalBytes || 0;
    console.log(`Working set ready: ${count.toLocaleString()} docs, ${+(datasetBytes / 1048576).toFixed(1)} MiB BSON; estimated cache fit is reported below.`);
    console.log('Cache and page counters are server-wide; cache-fit is an estimate, not measured residency for this collection.');
    console.log(`Report sources sync every ${Math.round(REPORT_SYNC_INTERVAL_MS / 60000)} minute(s); cache samples run every 10 seconds.${RUN_ONCE ? ' One-shot mode enabled.' : ' Stop with Ctrl+C.'}`);

    let previousCounters;
    let pendingSync = null;
    let nextReportSync = 0;
    let completedSamples = 0;
    while (true) {
      const now = Date.now();
      if (now >= nextReportSync && !pendingSync) {
        pendingSync = syncReports(db).finally(() => { pendingSync = null; });
        nextReportSync = now + REPORT_SYNC_INTERVAL_MS;
      }

      for (let index = 0; index < READS_PER_SAMPLE; index++) {
        const sequence = Math.floor(Math.random() * DOCUMENT_COUNT);
        await collection.findOne({ seq: sequence }, { projection: { seq: 1, payload: 1 } });
      }

      const status = await db.admin().command({ serverStatus: 1 });
      const cache = status.wiredTiger?.cache;
      if (!cache) throw new Error('MongoDB serverStatus did not return WiredTiger cache metrics.');

      const cacheBytes = cache['bytes currently in the cache'] || 0;
      const maxCacheBytes = cache['maximum bytes configured'] || 0;
      const pagesRead = cache['pages read into cache'] || 0;
      const pagesRequested = cache['pages requested from the cache'] || 0;
      const deltaRead = previousCounters ? Math.max(0, pagesRead - previousCounters.pagesRead) : null;
      const deltaRequested = previousCounters ? Math.max(0, pagesRequested - previousCounters.pagesRequested) : null;
      const hitPct = deltaRequested > 0
        ? +Math.max(0, 1 - deltaRead / deltaRequested).toFixed(4) * 100
        : null;
      const cacheFitPct = datasetBytes && maxCacheBytes
        ? +Math.min(100, maxCacheBytes / datasetBytes * 100).toFixed(2)
        : null;

      const sample = {
        type: "cache-sample", at: new Date(),
        intervalMs: previousCounters ? now - previousCounters.at : null,
        reportMetadataCount: reportRows.length,
        averageDocumentBytes: count ? datasetBytes / count : 0,
        cacheUsePct: maxCacheBytes ? 100 * cacheBytes / maxCacheBytes : null,
        collectionDocuments: count,
        collectionBsonMiB: +(datasetBytes / 1048576).toFixed(2),
        maximumDocumentBytes: sizeResult[0]?.maxBytes || 0,
        cacheUsedMiB: +(cacheBytes / 1048576).toFixed(1),
        cacheCapacityMiB: +(maxCacheBytes / 1048576).toFixed(1),
        estimatedDatasetCacheFitPct: cacheFitPct,
        pagesReadDelta10s: deltaRead,
        pagesRequestedDelta10s: deltaRequested,
        approximateCacheHitPct: hitPct
      };
      console.log(JSON.stringify(sample));
      record(sample);
      previousCounters = { pagesRead, pagesRequested, at: now };
      completedSamples++;
      if (RUN_ONCE && completedSamples >= 2) { if (pendingSync) await pendingSync; break; }
      await new Promise(resolve => setTimeout(resolve, Math.max(0, SAMPLE_INTERVAL_MS - (Date.now() - now))));
    }
  } finally {
    await client.close();
  }
})().catch(error => {
  console.error('Working-set exercise failed (check MongoDB and serverStatus privileges):', error.message);
  process.exit(1);
});
