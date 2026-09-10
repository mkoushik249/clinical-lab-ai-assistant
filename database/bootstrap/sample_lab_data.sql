CREATE TABLE IF NOT EXISTS departments (
    department_id SERIAL PRIMARY KEY,
    department_name VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS lab_tests (
    lab_test_id SERIAL PRIMARY KEY,
    test_code VARCHAR(50) NOT NULL UNIQUE,
    test_name VARCHAR(200) NOT NULL,
    department_id INTEGER NOT NULL REFERENCES departments(department_id),
    specimen_type VARCHAR(100) NOT NULL,
    turnaround_hours INTEGER,
    active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS test_aliases (
    alias_id SERIAL PRIMARY KEY,
    lab_test_id INTEGER NOT NULL REFERENCES lab_tests(lab_test_id),
    alias_name VARCHAR(200) NOT NULL
);

INSERT INTO departments (department_name)
VALUES
    ('Hematology'),
    ('Chemistry'),
    ('Microbiology')
ON CONFLICT DO NOTHING;

INSERT INTO lab_tests (
    test_code,
    test_name,
    department_id,
    specimen_type,
    turnaround_hours
)
VALUES
    (
        'CBC',
        'Complete Blood Count',
        (SELECT department_id FROM departments WHERE department_name = 'Hematology'),
        'Whole Blood',
        4
    ),
    (
        'CMP',
        'Comprehensive Metabolic Panel',
        (SELECT department_id FROM departments WHERE department_name = 'Chemistry'),
        'Serum',
        6
    ),
    (
        'BCULT',
        'Blood Culture',
        (SELECT department_id FROM departments WHERE department_name = 'Microbiology'),
        'Blood',
        48
    )
ON CONFLICT (test_code) DO NOTHING;

INSERT INTO test_aliases (lab_test_id, alias_name)
SELECT lab_test_id, 'CBC Panel'
FROM lab_tests
WHERE test_code = 'CBC';

INSERT INTO test_aliases (lab_test_id, alias_name)
SELECT lab_test_id, 'Metabolic Panel'
FROM lab_tests
WHERE test_code = 'CMP';