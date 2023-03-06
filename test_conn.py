import psycopg2


def postgres_test():
    conn = psycopg2.connect("dbname='accessibility_monitoring_app' user='postgres' host='db-local-to-delete.ctkjhkvedmur.eu-west-2.rds.amazonaws.com' password='O1TIjScF437' connect_timeout=1 ")
    conn.close()

postgres_test()
