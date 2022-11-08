-- DIALECT: bigquery
-- ENTITY: team_id
-- DOMAIN: taxonomy
WITH T1 AS (
    SELECT
        LMT.idx,
        T.league_alias AS league,
        T.conf_alias AS conference,
        T.division_alias AS division
    FROM
        {LEFTMOST_TABLE} AS LMT
        LEFT JOIN bigquery-public-data.ncaa_basketball.mbb_teams AS T
            ON LMT.team_id = T.id
)
SELECT
    T1.idx,
    T1.league,
    T1.conference,
    T1.division
FROM
    T1
GROUP BY
    T1.idx,
    T1.league,
    T1.conference,
    T1.division