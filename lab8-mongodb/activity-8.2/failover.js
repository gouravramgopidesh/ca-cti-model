// Run on current primary; shell may disconnect during step-down.
printjson(rs.status());
printjson(rs.stepDown(30,10));
