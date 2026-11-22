// Run in mongosh connected to the lab7-mongodb database.
for (const name of db.getCollectionNames()) {
  const rows = db.getCollection(name).aggregate([
    {$project:{bytes:{$bsonSize:'$$ROOT'}}},
    {$group:{_id:null,count:{$sum:1},averageBytes:{$avg:'$bytes'},maxBytes:{$max:'$bytes'},minBytes:{$min:'$bytes'}}}
  ]).toArray();
  printjson({collection:name, statistics:rows[0] || null, percentOfLimit:rows.length ? 100*rows[0].maxBytes/16777216 : null});
}
