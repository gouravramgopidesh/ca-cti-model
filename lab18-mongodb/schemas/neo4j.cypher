CREATE CONSTRAINT threat_key IF NOT EXISTS FOR (n:Threat) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT source_key IF NOT EXISTS FOR (n:Source) REQUIRE n.name IS UNIQUE;
CREATE CONSTRAINT indicator_key IF NOT EXISTS FOR (n:Indicator) REQUIRE n.value IS UNIQUE;
CREATE CONSTRAINT network_key IF NOT EXISTS FOR (n:Network) REQUIRE n.prefix IS UNIQUE;
CREATE CONSTRAINT community_key IF NOT EXISTS FOR (n:Community) REQUIRE n.id IS UNIQUE;
CREATE INDEX threat_history IF NOT EXISTS FOR (t:Threat) ON (t.from_source,t.timestamp);
CREATE INDEX threat_type_day IF NOT EXISTS FOR (t:Threat) ON (t.threat_type,t.day);
CREATE INDEX threat_day IF NOT EXISTS FOR (t:Threat) ON (t.day);
// (:Source)-[:REPORTED]->(:Threat)-[:OBSERVES]->(:Indicator)-[:IN_NETWORK]->(:Network)
// (:Source)-[:SUSPICIOUS {shared_indicators}]->(:Source)
// (:Threat)-[:IN_COMMUNITY]->(:Community)
