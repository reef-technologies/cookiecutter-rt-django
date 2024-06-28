def test__example_postgres(postgresql):
    cur = postgresql.cursor()
    cur.execute("CREATE TABLE test (id serial PRIMARY KEY, num integer, data varchar);")
    postgresql.commit()
    cur.close()
