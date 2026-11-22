// Optional mongosh indexes for the lab database; application also initializes indexes.
db.articles.createIndex({publishedAt:-1});
db.articles.createIndex({severity:1,category:1});
db.articles.createIndex({title:'text',summary:'text',tags:'text'});
db.articles.createIndex({canonicalUrl:1},{unique:true,partialFilterExpression:{canonicalUrl:{$type:'string'}}});
db.sources.createIndex({name:1},{unique:true});
db.indicators.createIndex({value:1},{unique:true});
db.annualReports.createIndex({url:1},{unique:true});
db.workingSet.createIndex({seq:1});
