require('dotenv').config();
const { MongoClient } = require('mongodb');
const { sources: sampleSources, buildArticles } = require('./data');
const { feeds, syncIntelligence } = require('./intelligence');

async function seed() {
  const client = new MongoClient(process.env.MONGODB_URI || 'mongodb://127.0.0.1:27017');
  try {
    await client.connect();
    const db = client.db(process.env.DB_NAME || 'lab7-mongodb');
    await Promise.all(['articles', 'sources', 'indicators', 'annualReports'].map(name =>
      db.collection(name).deleteMany({})
    ));

    const sourceCatalog = [...new Map(
      [...sampleSources, ...feeds.map(feed => ({
        name: feed.name,
        type: 'rss',
        url: feed.url,
        reliability: null
      }))].map(source => [source.name, source])
    ).values()];
    await db.collection('sources').insertMany(sourceCatalog);
    await db.collection('articles').insertMany(buildArticles(40));
    await db.collection('indicators').insertMany([
      { value: 'training-login.example.invalid', kind: 'domain', confidence: 70, category: 'phishing', firstSeen: new Date(), sourceName: 'Training dataset', isTrainingData: true },
      { value: '198.51.100.42', kind: 'ipv4', confidence: 60, category: 'command-and-control', firstSeen: new Date(), sourceName: 'Training dataset', isTrainingData: true },
      { value: 'https://example.invalid/update', kind: 'url', confidence: 55, category: 'malware-delivery', firstSeen: new Date(), sourceName: 'Training dataset', isTrainingData: true },
      { value: 'd41d8cd98f00b204e9800998ecf8427e', kind: 'md5', confidence: 50, category: 'malware', firstSeen: new Date(), sourceName: 'Training dataset', isTrainingData: true }
    ]);
    await db.collection('annualReports').insertOne({
      title: 'Annual Cybersecurity Outlook — sample record',
      organization: 'lab7-mongodb Demo',
      year: 2025,
      category: 'Global Threat Intelligence',
      url: 'https://github.com/jacobdjwilson/awesome-annual-security-reports/',
      summary: 'Demonstration record; use Sync sources & reports to check the public curated list.',
      discoveredAt: new Date(),
      isTrainingData: true
    });

    await Promise.all([
      db.collection('articles').createIndex({ publishedAt: -1 }),
      db.collection('articles').createIndex({ severity: 1, category: 1 }),
      db.collection('articles').createIndex({ title: 'text', summary: 'text', tags: 'text' }),
      db.collection('articles').createIndex(
        { canonicalUrl: 1 },
        { unique: true, partialFilterExpression: { canonicalUrl: { $type: 'string' } } }
      ),
      db.collection('indicators').createIndex({ value: 1 }, { unique: true }),
      db.collection('sources').createIndex({ name: 1 }, { unique: true }),
      db.collection('annualReports').createIndex({ url: 1 }, { unique: true })
    ]);

    console.log('Seeded lab7-mongodb sample data and indexes.');
    try {
      const result = await syncIntelligence(db);
      console.log(`Imported ${result.articles.added || 0} new CTI articles and ${result.reports.added || 0} annual reports.`);
      if (result.articles.failures?.length) console.warn(`${result.articles.failures.length} RSS feeds could not be reached.`);
      if (result.articles.error) console.warn(`CTI RSS sync failed: ${result.articles.error}`);
      if (result.reports.error) console.warn(`Annual report sync failed: ${result.reports.error}`);
    } catch (error) {
      console.warn(`Live data sync skipped: ${error.message}`);
    }
  } finally {
    await client.close();
  }
}

seed().catch(error => {
  console.error('Seed failed:', error);
  process.exit(1);
});
