"""Use PyMySQL as the MySQLdb driver so Django's mysql backend works."""
import pymysql

pymysql.install_as_MySQLdb()
