-- DIALECT: bigquery
-- ENTITY: game_id
-- DOMAIN: points
SELECT
    LMT.idx,
    G.points_game, 
    MAX(G.three_points_made) AS max_three_points_per_game,
    MAX(G.points_game) AS max_points_made_per_game
FROM
    {LEFTMOST_TABLE} AS LMT
    INNER JOIN bigquery-public-data.ncaa_basketball.mbb_teams_games_sr AS G
        ON LMT.game_id = G.game_id
WHERE
    season >= EXTRACT(YEAR FROM DATE(LMT.min_date))
    AND season <= EXTRACT(YEAR FROM DATE(LMT.max_date))
GROUP BY 
    LMT.idx