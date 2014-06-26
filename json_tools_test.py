from dtest import Tester, debug
import os

class TestJson(Tester):

    def json_tools_test(self):

        debug("Starting cluster...")
        cluster = self.cluster
        cluster.populate(1).start()

        debug("Version: " + cluster.version())

        debug("Getting CQLSH...")
        [node1] = cluster.nodelist()
        cursor = self.patient_cql_connection(node1).cursor()

        debug("Inserting data...")
        self.create_ks(cursor, 'Test', 1)

        cursor.execute("""
            CREATE TABLE users (
                user_name varchar PRIMARY KEY,
                password varchar,
                gender varchar,
                state varchar,
                birth_year bigint
            );
        """)

        cursor.execute("INSERT INTO Test. users (user_name, password, gender, state, birth_year) VALUES('frodo', 'pass@', 'male', 'CA', 1985);")
        cursor.execute("INSERT INTO Test. users (user_name, password, gender, state, birth_year) VALUES('sam', '@pass', 'male', 'NY', 1980);")

        cursor.execute("SELECT * FROM Test. users")
        res = cursor.fetchall()

        self.assertItemsEqual(res,
           [ [ u'frodo', 1985, u'male', u'pass@', u'CA' ],
              [u'sam', 1980, u'male', u'@pass', u'NY' ] ] )

        debug("Flushing and stopping cluster...")
        node1.flush()
        cluster.stop()

        debug("Exporting to JSON file...")
        with open("schema.json", "w") as out_file:
            node1.run_sstable2json(out_file)

        debug("Deleting cluster and creating new...")
        cluster.clear()
        cluster.start()

        debug("Inserting data...")
        cursor = self.patient_cql_connection(node1).cursor()
        self.create_ks(cursor, 'Test', 1)

        cursor.execute("""
            CREATE TABLE users (
                user_name varchar PRIMARY KEY,
                password varchar,
                gender varchar,
                state varchar,
                birth_year bigint
            );
        """)

        cursor.execute("INSERT INTO Test. users (user_name, password, gender, state, birth_year) VALUES('gandalf', 'p@$$', 'male', 'WA', 1955);")
        node1.flush()
        cluster.stop()

        debug("Importing JSON file...")

        node1.run_json2sstable("schema.json", "test", "users")
        os.remove("schema.json")

        debug("Verifying import...")
        cluster.start()
        [node1] = cluster.nodelist()
        cursor = self.patient_cql_connection(node1).cursor()

        cursor.execute("SELECT * FROM Test. users")
        res = cursor.fetchall()

        debug("data: " + str(res))

        self.assertItemsEqual(res,
           [ [ u'frodo', 1985, u'male', u'pass@', u'CA' ],
                [u'sam', 1980, u'male', u'@pass', u'NY' ],
                [u'gandalf', 1955, u'male', u'p@$$', u'WA'] ] )
