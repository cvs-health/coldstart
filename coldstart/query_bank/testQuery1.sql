-- DIALECT: bigquery
-- ENTITY: team_id
-- DOMAIN: wins
WITH T1 AS (
    SELECT
        LMT.idx,
        CASE
            WHEN G.win = True Then 1
            ELSE 0
        END AS win_count
    FROM
        {LEFTMOST_TABLE} AS LMT
        LEFT JOIN bigquery-public-data.ncaa_basketball.mbb_teams AS T
            ON LMT.team_id = T.id
        LEFT JOIN bigquery-public-data.ncaa_basketball.mbb_historical_teams_games AS G
            ON T.id = G.team_id
    WHERE
        season >= EXTRACT(YEAR FROM DATE(LMT.min_date))
        AND season <= EXTRACT(YEAR FROM DATE(LMT.max_date))
)
SELECT
    T1.idx,
    SUM(T1.win_count) AS win_count
FROM
    T1
GROUP BY
    T1.idx