# coding:utf-8
try:
    import MySQLdb
except:
    import mysql.connector as MySQLdb

try:
    conn = MySQLdb.connect(host="127.0.0.1", db="sdk", user="root", passwd="1213")

    print(conn)
    print("----")
    print(conn.cursor())
except Exception as e:
    print(e)
