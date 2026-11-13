import csv
import sqlite3
import os

import pandas as pd

def create_db():
    os.makedirs('db', exist_ok=True)
    conn = sqlite3.connect(os.path.join('db', 'custom_dict.db'))

    # simplified,traditional,pinyin,polish,english

    conn.execute('''CREATE TABLE IF NOT EXISTS custom_dict (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    simplified TEXT NOT NULL,
                    traditional TEXT,
                    pinyin TEXT,
                    polish TEXT,
                    english TEXT
                )''')

    conn.close()

def update_db():
    conn = sqlite3.connect(os.path.join('db', 'custom_dict.db'))

    # clear all (temp. solution)
    conn.execute("DELETE FROM custom_dict")

    # load all CSV files
    csv_files = [f for f in os.listdir('custom_dict') if f.endswith('.csv')]

    for file in csv_files:
        df = pd.read_csv(os.path.join("custom_dict", file))
        df.to_sql('custom_dict', conn, if_exists='append', index=False)

        # print(pd.read_sql('''SELECT * FROM custom_dict''', conn))

    conn.close()
    

if __name__ == "__main__":
    create_db()

    update_db()