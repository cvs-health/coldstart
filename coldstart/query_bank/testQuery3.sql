-- DIALECT: bigquery
-- ENTITY: team_id
-- DOMAIN: mascot
WITH T1 AS (
    SELECT
        LMT.idx,
        M.mascot_common_name AS mascot_common_name,
        M.tax_subspecies AS tax_subspecies,
        M.tax_species AS tax_species,
        M.tax_genus AS tax_genus,
        M.tax_family AS tax_family,
        M.tax_order AS tax_order,
        M.tax_class AS tax_class,
        M.tax_phylum AS tax_phylum,
        M.tax_kingdom AS tax_kingdom,
        M.tax_domain AS tax_domain,
        M.non_tax_type AS non_tax_type
    FROM
        {LEFTMOST_TABLE} AS LMT
        LEFT JOIN bigquery-public-data.ncaa_basketball.mbb_teams AS T
            ON LMT.team_id = T.id
        LEFT JOIN bigquery-public-data.ncaa_basketball.mascots AS M
            ON T.id = M.id
)
SELECT
    T1.idx,
    T1.mascot_common_name,
    T1.tax_subspecies,
    T1.tax_species,
    T1.tax_genus,
    T1.tax_family,
    T1.tax_order,
    T1.tax_class,
    T1.tax_phylum,
    T1.tax_kingdom,
    T1.tax_domain,
    T1.non_tax_type
FROM
    T1
GROUP BY
    T1.idx,
    T1.mascot_common_name,
    T1.tax_subspecies,
    T1.tax_species,
    T1.tax_genus,
    T1.tax_family,
    T1.tax_order,
    T1.tax_class,
    T1.tax_phylum,
    T1.tax_kingdom,
    T1.tax_domain,
    T1.non_tax_type
