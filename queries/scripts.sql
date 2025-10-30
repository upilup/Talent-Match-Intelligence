-- =============================================================
-- STEP 2: Operationalize the Logic in SQL
-- Purpose: Calculate how closely each employee matches the
--          benchmark employees (rating = 5) for a given role.
--
-- =============================================================

-- ----------------------------------------------------------------------
-- CTE 1: Create unified view of all employee scores
-- ----------------------------------------------------------------------
WITH employee_scores AS (
    SELECT
        employee_id::text AS employee_id,
        'Cognitive' AS tgv_name,
        'IQ' AS tv_name,
        iq AS score,
        TRUE AS is_numeric,
        'higher' AS scoring_direction
    FROM profiles_psych

    UNION ALL
    SELECT
        employee_id::text AS employee_id,
        'Cognitive' AS tgv_name,
        'GTQ_Total' AS tv_name,
        gtq AS score,
        TRUE, 'higher'
    FROM profiles_psych

    UNION ALL
    SELECT
        employee_id::text AS employee_id,
        'Behavioral' AS tgv_name,
        scale_code AS tv_name,
        score,
        TRUE, 'higher'
    FROM papi_scores

    UNION ALL
    SELECT
        employee_id::text AS employee_id,
        'Competency' AS tgv_name,
        pillar_code AS tv_name,
        score,
        TRUE, 'higher'
    FROM competencies_yearly

    UNION ALL
    SELECT
        employee_id::text AS employee_id,
        'Strength' AS tgv_name,
        theme AS tv_name,
        rank AS score,
        TRUE, 'lower' -- Ranks: lower score (rank) is better
    FROM strengths
),

-- ----------------------------------------------------------------------
-- CTE 2: Select Benchmark IDs 
-- ----------------------------------------------------------------------
benchmark_selection AS (
    SELECT
        e.employee_id -- Select the full EMP/DUP ID from the employees table
    FROM talent_benchmarks tb
    -- Unnest the numeric/base IDs from the talent_benchmarks array
    JOIN LATERAL unnest(tb.selected_talent_ids) AS base_id_numeric(id) ON TRUE
    -- Join to the employees table by matching the numeric part of the employee_id
    -- This handles both EMP and DUP prefixes correctly by matching the end of the string.
    JOIN employees e ON e.employee_id LIKE ('%' || base_id_numeric.id::text)
    WHERE tb.job_vacancy_id = :job_vacancy_id 
),

-- ----------------------------------------------------------------------
-- CTE 3: Compute median baseline score per TV (using only benchmark employees)
-- ----------------------------------------------------------------------
baseline AS (
    SELECT
        es.tgv_name,
        es.tv_name,
        es.scoring_direction, 
        es.is_numeric,       
        -- Calculate the median score for the benchmark group
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY es.score) AS baseline_score
    FROM employee_scores es
    JOIN benchmark_selection b
    ON es.employee_id = b.employee_id
    GROUP BY es.tgv_name, es.tv_name, es.scoring_direction, es.is_numeric
),

-- ----------------------------------------------------------------------
-- CTE 4: Compute TV-level match % for all employees vs. benchmark
-- ----------------------------------------------------------------------
tv_match AS (
    SELECT
        es.employee_id,
        es.tgv_name,
        es.tv_name,
        b.baseline_score,
        es.score AS user_score,
        b.scoring_direction,
        -- Calculation logic for tv_match_rate
        CASE
            WHEN b.is_numeric THEN
                CASE
                    -- Higher score is better
                    WHEN b.scoring_direction = 'higher'
                        THEN ROUND((es.score::numeric / b.baseline_score::numeric * 100), 2)
                    -- Lower score is better (Strengths Rank)
                    -- Formula: ((2 * Baseline - UserScore) / Baseline) * 100
                    WHEN b.scoring_direction = 'lower'
                        THEN ROUND((((2 * b.baseline_score::numeric - es.score::numeric) / b.baseline_score::numeric) * 100), 2)
                    ELSE 0.0
                END
            ELSE 0.0 -- Default for non-numeric if no match
        END AS tv_match_rate
    FROM employee_scores es
    -- LEFT JOIN to include all employees, even if a baseline doesn't exist for every TV
    LEFT JOIN baseline b USING (tgv_name, tv_name)
    -- We only want results where a valid benchmark (baseline) was found
    WHERE b.baseline_score IS NOT NULL
),

-- ----------------------------------------------------------------------
-- CTE 5: Compute average TGV match % (Employee x TGV)
-- ----------------------------------------------------------------------
tgv_match AS (
    SELECT
        employee_id,
        tgv_name,
        ROUND(AVG(tv_match_rate)::numeric, 2) AS tgv_match_rate
    FROM tv_match
    GROUP BY employee_id, tgv_name
),

-- ----------------------------------------------------------------------
-- CTE 6: Compute overall final match % per employee
-- ----------------------------------------------------------------------
final_match AS (
    SELECT
        employee_id,
        ROUND(AVG(tgv_match_rate)::numeric, 2) AS final_match_rate
    FROM tgv_match
    GROUP BY employee_id
)

-- ==========================================================
-- FINAL SELECT: Combine all data with employee metadata (expected output)
-- ==========================================================

SELECT
    tv.employee_id,
    e.fullname AS name, -- Changed from e.name to e.fullname based on ERD/data
    d.name AS department, 
    p.name AS role,
    g.name AS grade,
    tv.tgv_name,
    tv.tv_name,
    tv.baseline_score,
    tv.user_score,
    tv.scoring_direction,
    tv.tv_match_rate,
    tg.tgv_match_rate,
    f.final_match_rate
FROM tv_match tv
JOIN tgv_match tg USING (employee_id, tgv_name)
JOIN final_match f USING (employee_id)
JOIN employees e USING (employee_id)
JOIN dim_directorates d ON e.directorate_id = d.directorate_id
JOIN dim_positions p ON e.position_id = p.position_id
JOIN dim_grades g ON e.grade_id = g.grade_id
ORDER BY f.final_match_rate DESC;