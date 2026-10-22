from __future__ import annotations

import unittest

from base.tools import is_read_only


class GuardTests(unittest.TestCase):
    def test_read_only(self) -> None:
        cases = (
            "SELECT 1",
            "SELECT 1;",
            "SELECT 'delete' AS word",
            "SELECT '--' AS marker",
            "SELECT '/* comment */' AS marker",
            "SELECT \"a;b\" AS marker",
            "SELECT 1 /* ; DROP TABLE orders; */",
            "SELECT 1 /*'*/",
            "SELECT CASE WHEN 1 = 1 THEN 1 ELSE 0 END",
            "SELECT a + b FROM orders",
            "SELECT DISTINCT a",
            "SELECT DATE '2024-01-01'",
            "SELECT INTERVAL '1 day'",
            "SELECT ARRAY[1, 2]",
            "SELECT TOP 10 * FROM orders",
            "-- note\nSELECT 1",
            "SELECT 1 -- trailing note",
            "SHOW LIGHTNING DATABASES",
            "SHOW CREATE TABLE orders",
            "WITH x AS (SELECT 1) SELECT * FROM x",
            "EXPLAIN SELECT * FROM orders",
        )
        for sql in cases:
            with self.subTest(sql=sql):
                self.assertTrue(is_read_only(sql))

    def test_blocked(self) -> None:
        cases = (
            "DELETE FROM orders",
            "SELECT 1; DROP TABLE orders",
            "SELECT '--' AS marker; DROP TABLE orders",
            "SELECT '/*' AS marker; DROP TABLE orders /* */",
            "SELECT `--` AS marker; DROP TABLE orders",
            "SELECT 1 /*'*/ ; DROP TABLE orders; --'*/",
            "SELECT 1 /*\"*/ ; DROP TABLE orders; --\"*/",
            "SELECT 1 /*`*/ ; DROP TABLE orders; --`*/",
            r"SELECT 'it\'s'; DROP TABLE orders;",
            r'SELECT "it\"s"; DROP TABLE orders;',
            r"SELECT `it\`s`; DROP TABLE orders;",
            "SHOW CREATE TABLE orders DROP TABLE orders",
            "SHOW CREATE TABLE orders; DROP TABLE orders",
            "EXPLAIN DELETE FROM orders",
            "INSERT INTO orders VALUES (1)",
            # Spark backtick and double-quote tokens do not use backslash escapes.
            "SELECT `x\\` FROM t; DROP TABLE t; -- `",
            'SELECT "x\\" FROM t; DROP TABLE t; -- "',
            "SELECT 'unterminated; DROP TABLE t",
            # Spark functions that call arbitrary Java or have side effects.
            "SELECT reflect('java.lang.Runtime', 'getRuntime')",
            "SELECT java_method('java.lang.System', 'exit', 0)",
            "SELECT assert_true(1 = 0)",
            "SELECT raise_error('stop')",
            # Spark and Hive statements that write, load or run code.
            "SELECT TRANSFORM(a) USING 'cat' AS (b) FROM t",
            "SELECT TRANSFORM (a, b) USING \"python s.py\" FROM t",
            "INSERT OVERWRITE DIRECTORY '/tmp/x' SELECT 1",
            "ADD JAR '/tmp/x.jar'",
            "ADD FILE '/tmp/x.py'",
            "CACHE TABLE t",
            "UNCACHE TABLE t",
            "REFRESH TABLE t",
            "LOAD DATA INPATH '/tmp/x' INTO TABLE t",
            "MSCK REPAIR TABLE t",
            "ANALYZE TABLE t COMPUTE STATISTICS",
            "SET spark.sql.ansi.enabled=true",
            "RESET",
        )
        for sql in cases:
            with self.subTest(sql=sql):
                self.assertFalse(is_read_only(sql))


if __name__ == "__main__":
    unittest.main()
