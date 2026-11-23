// Run on mongo1 before running the Python verification.
try { rs.conf(); print('Already initialized'); }
catch (e) {
  if (e.code !== 94 && e.codeName !== 'NotYetInitialized') throw e;
  const result = rs.initiate({_id:'rs0',members:[
    {_id:0,host:'mongo1:27017',priority:2},
    {_id:1,host:'mongo2:27017',priority:1},
    {_id:2,host:'mongo3:27017',priority:1}]});
  printjson(result); if (!result.ok) quit(1);
}
printjson(rs.conf());
printjson(rs.status());
