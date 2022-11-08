-- DIALECT: bigquery
-- ENTITY: team_id
-- DOMAIN: venue
WITH T1 AS (
    SELECT
        LMT.idx,
        T.venue_state,
        T.venue_city,
        T.venue_capacity
    FROM
        {LEFTMOST_TABLE} AS LMT
        LEFT JOIN bigquery-public-data.ncaa_basketball.mbb_teams AS T
            ON LMT.team_id = T.id
)
SELECT
    T1.idx,
    T1.venue_state,
    T1.venue_city,
    T1.venue_capacity
FROM
    T1
GROUP BY
    T1.idx,
    T1.venue_state,
    T1.venue_city,
    T1.venue_capacity