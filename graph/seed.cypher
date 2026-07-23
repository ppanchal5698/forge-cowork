// Task-graph / knowledge-graph baseline schema — identical in dev and prod.
// Apply: docker compose exec neo4j cypher-shell -u neo4j -p forgelocal -f /seed/seed.cypher
CREATE CONSTRAINT tenant_id_unique IF NOT EXISTS FOR (t:Tenant) REQUIRE t.tenant_id IS UNIQUE;
CREATE CONSTRAINT task_id_unique IF NOT EXISTS FOR (t:Task) REQUIRE t.task_id IS UNIQUE;
CREATE CONSTRAINT run_id_unique IF NOT EXISTS FOR (r:AgentRun) REQUIRE r.run_id IS UNIQUE;
CREATE CONSTRAINT artifact_id_unique IF NOT EXISTS FOR (a:Artifact) REQUIRE a.artifact_id IS UNIQUE;
