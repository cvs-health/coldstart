-- DIALECT: bigquery
-- ENTITY: team_id
-- DOMAIN: losses
WITH T1 AS (
    SELECT
        LMT.idx,
        CASE
            WHEN G.win = False Then 1
            ELSE 0
        END AS loss_count
    FROM
        {LEFTMOST_TABLE} AS LMT
        INNER JOIN bigquery-public-data.ncaa_basketball.mbb_teams AS T
            ON LMT.team_id = T.id
        LEFT JOIN bigquery-public-data.ncaa_basketball.mbb_historical_teams_games AS G
            ON T.id = G.team_id
    WHERE
        season >= EXTRACT(YEAR FROM DATE(LMT.min_date))
        AND season <= EXTRACT(YEAR FROM DATE(LMT.max_date))
)
SELECT
    T1.idx,
    SUM(T1.loss_count) AS loss_count
FROM
    T1
GROUP BY
    T1.idx