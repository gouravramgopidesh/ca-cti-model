require('dotenv').config();
const { MongoClient } = require('mongodb');
const { syncIntelligence } = require('./intelligence');

async function main() {
  const client = new MongoClient(process.env.MONGODB_URI || 'mongodb://127.0.0.1:27017');
  try {
    await client.connect();
    const db = client.db(process.env.DB_NAME || 'lab7-mongodb');
    const result = await syncIntelligence(db);
    console.log(JSON.stringify(result, null, 2));
    if (result.articles.error || result.reports.error) process.exitCode = 1;
  } finally {
    await client.close();
  }
}

main().catch(error => {
  console.error('Intelligence sync failed:', error.message);
  process.exit(1);
});
