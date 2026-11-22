// Non-destructive Lab 7.1 experiment using a snapshot of the existing articles.
require('dotenv').config();
const { MongoClient } = require('mongodb');
const { performance } = require('node:perf_hooks');
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const valid = new Set(['confirmed-threat', 'benign', 'needs-review']);
async function main() {
  const client = new MongoClient(process.env.MONGODB_URI || 'mongodb://127.0.0.1:27017');
  try {
    await client.connect();
    const db = client.db(process.env.DB_NAME || 'lab7-mongodb');
    const articles = await db.collection('articles').find({}).toArray();
    if (!articles.length) throw new Error('No articles found. Start your existing application or restore its database first.');
    const catalog = new Map((await db.collection('sources').find({}).toArray()).map(s => [s.name, s]));
    const run = `lab71_${Date.now()}`;
    const ref = db.collection(`${run}_referenced`), embedded = db.collection(`${run}_embedded`), sources = db.collection(`${run}_sources`), assessments = db.collection(`${run}_assessments`);
    const sourceRows = new Map(), refRows = [], embRows = [], assessmentRows = [];
    for (const a of articles) {
      const key = String(a.sourceId || a.sourceName || 'Unknown');
      const s = catalog.get(key) || a.source || {};
      const publisher = { name: s.name || key, url: s.url || a.sourceUrl || null, type: s.type || null, reliability: s.reliability ?? null };
      if (!sourceRows.has(key)) sourceRows.set(key, { _id: key, ...publisher });
      const verdict = a.sourceAssessment?.verdict || a.classification;
      const assessment = { verdict: valid.has(verdict) ? verdict : 'needs-review', reviewedAt: a.sourceAssessment?.reviewedAt || a.reviewedAt || null };
      const base = { _id: a._id, title: a.title || '', category: a.category || null, isTrainingData: a.isTrainingData === true };
      refRows.push({ ...base, sourceId: key, assessmentId: a._id });
      assessmentRows.push({ _id: a._id, ...assessment });
      const { _id, ...snapshot } = sourceRows.get(key);
      embRows.push({ ...base, source: snapshot, sourceAssessment: assessment });
    }
    await sources.insertMany([...sourceRows.values()]);
    await assessments.insertMany(assessmentRows);
    await ref.insertMany(refRows);
    await embedded.insertMany(embRows);
    await assessments.createIndex({ verdict: 1 });
    await ref.createIndex({ sourceId: 1 });
    await ref.createIndex({ assessmentId: 1 });
    await embedded.createIndex({ 'sourceAssessment.verdict': 1 });
    await embedded.createIndex({ 'source.name': 1 });
    const joins = [
      { $lookup: { from: assessments.collectionName, localField: 'assessmentId', foreignField: '_id', as: 'sourceAssessment' } },
      { $unwind: '$sourceAssessment' },
      { $lookup: { from: sources.collectionName, localField: 'sourceId', foreignField: '_id', as: 'source' } },
      { $unwind: '$source' }
    ];
    const projection = { $project: { _id: 1, title: 1, isTrainingData: 1, publisher: '$source.name', verdict: '$sourceAssessment.verdict' } };
    const verdicts = ['confirmed-threat', 'benign', 'needs-review'];
    const scenarios = verdicts.map(verdict => ({ name: verdict, r: [...joins.slice(0,2), { $match: { 'sourceAssessment.verdict': verdict } }, ...joins.slice(2), projection], e: [{ $match: { 'sourceAssessment.verdict': verdict } }, projection] }));
    scenarios.push({ name: 'article-detail', r: [{ $match: { _id: articles[0]._id } }, ...joins, projection], e: [{ $match: { _id: articles[0]._id } }, projection] });
    const benchmark = [];
    const sorted = rows => rows.sort((a,b) => String(a._id).localeCompare(String(b._id)));
    const measure = async (col, pipeline) => { const start = performance.now(); const rows = await col.aggregate(pipeline).toArray(); return { ms: performance.now() - start, rows }; };
    const median = values => { const v = [...values].sort((a,b)=>a-b); return (v[9]+v[10])/2; };
    for (const test of scenarios) {
      const r = await measure(ref,test.r), e = await measure(embedded,test.e);
      assert.deepEqual(sorted(r.rows),sorted(e.rows),`Different query outputs: ${test.name}`);
      const rt=[], et=[];
      for(let i=0;i<20;i++) {
        if(i%2===0) { rt.push((await measure(ref,test.r)).ms); et.push((await measure(embedded,test.e)).ms); }
        else { et.push((await measure(embedded,test.e)).ms); rt.push((await measure(ref,test.r)).ms); }
      }
      benchmark.push({ query:test.name, matchingRows:r.rows.length, referencedMedianMs:median(rt), embeddedMedianMs:median(et) });
    }
    const sizes = {};
    for (const col of [ref, embedded, sources, assessments]) {
      sizes[col.collectionName] = (await col.aggregate([{ $project:{ bytes:{ $bsonSize:'$$ROOT' } } },{ $group:{ _id:null,count:{ $sum:1 },averageBytes:{ $avg:'$bytes' },maxBytes:{ $max:'$bytes' },totalBytes:{ $sum:'$bytes' } } }]).toArray())[0];
      sizes[col.collectionName].percentOf16MiB = sizes[col.collectionName].maxBytes / 16777216 * 100;
    }
    const report = { run, database:db.databaseName, date:new Date(), articleCount:articles.length, trainingCount:embRows.filter(x=>x.isTrainingData).length, example:{ referenced:refRows[0], embedded:embRows[0], assessment:assessmentRows[0], source:[...sourceRows.values()][0] }, benchmark, sizes, notes:'20 alternating warm-cache runs per query; includes client round trip. Results depend on data, indexes, server load and cache. Verdict is about reported activity, not publisher identity. Zero-row cases do not demonstrate retrieval speed for matching records.' };
    const dir = path.join(__dirname,'..','evidence'); fs.mkdirSync(dir,{recursive:true});
    const output = path.join(dir,`${run}.json`); fs.writeFileSync(output,JSON.stringify(report,null,2));
    console.table(benchmark); console.log('Evidence:',output); console.log('Experiment collections:',Object.keys(sizes).join(', '));
  } finally { await client.close(); }
}
main().catch(err=>{console.error(err);process.exitCode=1;});
