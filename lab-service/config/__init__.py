# Allow Django's MySQL backend to use the pure-Python PyMySQL driver instead of
# the C-based mysqlclient (which needs system build tools). This lets one lab
# instance (e.g. Pathlabs Nepal) run on MySQL while others stay on PostgreSQL —
# proving the FHIR adapter is storage-engine agnostic. No-op when unused.
try:
    import pymysql

    pymysql.install_as_MySQLdb()
except ImportError:  # pragma: no cover - PyMySQL only needed for MySQL instances
    pass
