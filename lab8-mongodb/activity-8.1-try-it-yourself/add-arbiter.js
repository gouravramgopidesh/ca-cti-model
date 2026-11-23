// Run on current primary via replica set URI.
db.adminCommand({setDefaultRWConcern:1,defaultWriteConcern:{w:"majority"}});
if (!rs.conf().members.some(m=>m.host==="arbiter:27017")) printjson(rs.addArb("arbiter:27017"));
printjson(rs.status());
