import sqlite3

async def db_start():
    global db, cur

    db = sqlite3.connect('database.db')
    cur = db.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS appointment
    (
        date TEXT,
        time TEXT,
        free NUMERIC NOT NULL DEFAULT 1,
        name TEXT,
        tgId NUMERIC,
        username TEXT,
        telNumber TEXT
    )""")

    db.commit()


async def create_time(state):
    async with state.proxy() as data:
        exists = cur.execute('SELECT 1 FROM appointment WHERE date = ? AND time = ?', [data['date'], data['time']]).fetchone()
        if not exists:
            cur.execute('INSERT INTO appointment(date, time) VALUES(?, ?)', [data['date'], data['time']])
            db.commit()


# async def update_time(date, time):
#     is_free = cur.execute('SELECT free FROM appointment WHERE date = ? AND time = ?', [date, time]).fetchone()
#     if not is_free and is_free[0] == 1:
#         cur.execute('UPDATE appointment SET free = 0, name = ?, tgId = ?, telNumber = ? WHERE date = ? AND time = ?', [name, tg_id, tel_number, message, date, time])
#         db.commit()
#
# async def delete_time(data, time)
