-- One tournament per name: matches started with the same tournament_name share
-- its tournament_id. Before this, every match got a tournament row of its own.
-- Merge those into the earliest row of each name (by its first match), then
-- make the name unique. The lock keeps servers still running the old code
-- from adding rows while this runs; after it, their inserts of an existing
-- name fail until they are replaced.
LOCK TABLE tournament IN SHARE ROW EXCLUSIVE MODE;

CREATE TEMP TABLE tournament_merge ON COMMIT DROP AS
SELECT t.tournament_id,
       first_value(t.tournament_id) OVER (
           PARTITION BY t.tournament_name
           ORDER BY f.first_match NULLS LAST, t.tournament_id
       ) AS keep_id
FROM tournament t
LEFT JOIN LATERAL (
    SELECT min(m.created_at) AS first_match
    FROM match_data m
    WHERE m.tournament_id = t.tournament_id
) f ON true
WHERE t.tournament_name IS NOT NULL;

UPDATE match_data m
SET tournament_id = r.keep_id
FROM tournament_merge r
WHERE m.tournament_id = r.tournament_id
  AND r.tournament_id <> r.keep_id;

-- Only rows that no match points at any more (the FK cascades to match_data).
DELETE FROM tournament t
USING tournament_merge r
WHERE t.tournament_id = r.tournament_id
  AND r.tournament_id <> r.keep_id;

CREATE UNIQUE INDEX IF NOT EXISTS tournament_tournament_name_key
    ON tournament (tournament_name);
