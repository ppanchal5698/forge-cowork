from neo4j import GraphDatabase

from .config import settings

_driver = None


def driver():
    global _driver
    if _driver is None:
        _driver = GraphDatabase.driver(
            settings.neo4j_uri, auth=(settings.neo4j_user, settings.neo4j_password)
        )
    return _driver


# Task graph per agent run: task → run → step(s) → output (CLAUDE.md §6).
# tenant_id lives on every node (multi-tenancy §5).
_CYPHER = """
MERGE (t:Task {id: $task_id}) SET t.tenant_id = $tenant_id, t.title = $title
MERGE (r:AgentRun {id: $run_id}) SET r.tenant_id = $tenant_id, r.status = 'done'
MERGE (t)-[:HAS_RUN]->(r)
WITH r
UNWIND $steps AS step_name
  MERGE (s:Step {run_id: $run_id, name: step_name}) SET s.tenant_id = $tenant_id
  MERGE (r)-[:EXECUTED]->(s)
WITH DISTINCT r
MERGE (o:Output {run_id: $run_id}) SET o.tenant_id = $tenant_id, o.s3_key = $output_key
MERGE (r)-[:PRODUCED]->(o)
"""


def write_run_graph(tenant_id, task_id, title, run_id, steps, output_key):
    with driver().session() as session:
        session.run(
            _CYPHER,
            tenant_id=tenant_id,
            task_id=task_id,
            title=title,
            run_id=run_id,
            steps=steps,
            output_key=output_key,
        )
