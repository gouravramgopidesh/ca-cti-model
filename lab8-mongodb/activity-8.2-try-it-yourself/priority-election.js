// Run on current primary via replica set URI.
const current=db.hello().me, cfg=rs.conf();
const candidates=cfg.members.filter(m=>!m.arbiterOnly && m.host!==current && m.votes!==0);
candidates.forEach((m,i)=>m.priority=i===0?3:1);
cfg.members.find(m=>m.host===current).priority=4;
print('Prediction: '+candidates[0].host); printjson(rs.reconfig(cfg));
sleep(8000); printjson(rs.stepDown(60,10));
// Reconnect with replica set URI and run rs.status() to verify.
