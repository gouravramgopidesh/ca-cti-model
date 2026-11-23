const hosts = [0,1,2].map(i => `mongo-${i}.mongo-headless-svc.lab13-mongodb.svc.cluster.local:27017`);
try { rs.conf(); print('Replica set already initialized'); }
catch (e) { if (e.code !== 94) throw e; printjson(rs.initiate({_id:'rs0',members:hosts.map((host,_id)=>({_id,host}))})); }
