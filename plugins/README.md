# /plugins

Long-running / **stateful** tasks (scrapers, ETL, integrations). Deploy target: ECS tasks
in both dev and prod. Short stateless functions do not belong here — they go in `/skills`
(Lambda). See CLAUDE.md §6. First plugin lands in Sprint 2.
