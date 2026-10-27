CREATE CONSTRAINT unique_system_urn IF NOT EXISTS FOR (s:System) REQUIRE s.urn IS UNIQUE;
CREATE CONSTRAINT unique_resource_urn IF NOT EXISTS FOR (r:Resource) REQUIRE r.urn IS UNIQUE;
CREATE CONSTRAINT unique_actor_urn IF NOT EXISTS FOR (a:Actor) REQUIRE a.urn IS UNIQUE;
CREATE CONSTRAINT unique_role_urn IF NOT EXISTS FOR (ro:Role) REQUIRE ro.urn IS UNIQUE;
CREATE CONSTRAINT unique_step_urn IF NOT EXISTS FOR (p:ProcessStep) REQUIRE p.urn IS UNIQUE;
CREATE CONSTRAINT unique_doc_urn IF NOT EXISTS FOR (d:Document) REQUIRE d.urn IS UNIQUE;
CREATE CONSTRAINT unique_chunk_urn IF NOT EXISTS FOR (c:DocumentChunk) REQUIRE c.urn IS UNIQUE;
CREATE INDEX idx_resource_type IF NOT EXISTS FOR (r:Resource) ON (r.type);
CREATE INDEX idx_step_timestamp IF NOT EXISTS FOR (p:ProcessStep) ON (p.timestamp);
