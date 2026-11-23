CREATE KEYSPACE IF NOT EXISTS lab18_capstone WITH replication = {'class':'SimpleStrategy','replication_factor':1};
USE lab18_capstone;
CREATE TABLE IF NOT EXISTS threats_by_source (id text, from_source text, publisher text, timestamp bigint, day text, indicator text, network text, threat_type text, target text, source_url text, source_count int, timestamp_basis text, PRIMARY KEY ((from_source,day),timestamp,id)) WITH CLUSTERING ORDER BY (timestamp DESC,id ASC);
CREATE TABLE IF NOT EXISTS threats_by_type (id text, from_source text, publisher text, timestamp bigint, day text, indicator text, network text, threat_type text, target text, source_url text, source_count int, timestamp_basis text, PRIMARY KEY ((threat_type,day),timestamp,id)) WITH CLUSTERING ORDER BY (timestamp DESC,id ASC);
