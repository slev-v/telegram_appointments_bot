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
        phNumber TEXT
    )""")

    db.commit()


async def create_time(state):
    async with state.proxy() as data:
        exists = cur.execute('SELECT 1 FROM appointment WHERE date = ? AND time = ?',
                             [data['date'], data['time']]).fetchone()
        if not exists:
            cur.execute('INSERT INTO appointment(date, time) VALUES(?, ?)', [data['date'], data['time']])
            db.commit()


async def get_date(target):
    if target == 'update':
        fetch = cur.execute('SELECT date FROM appointment WHERE free = ?', [1, ]).fetchall()
    else:
        fetch = cur.execute('SELECT date FROM appointment').fetchall()
    dates = []
    for row in fetch:
        dates.append(row[0])
    return dates


async def get_time(date):
    fetch = cur.execute('SELECT time FROM appointment WHERE date = ?', [date]).fetchall()
    times = []
    for row in fetch:
        times.append(row[0])
    return times


async def free_check(state):
    async with state.proxy() as data:
        free = cur.execute('SELECT free FROM appointment WHERE date = ? AND time = ?',
                           [data['date'], data['time']]).fetchone()
        return free[0]


async def delete_time(state):
    async with state.proxy() as data:
        cur.execute('DELETE FROM appointment WHERE date = ? AND time = ?', [data['date'], data['time']])
        db.commit()


async def update_appointment(state):
    async with state.proxy() as data:
        cur.execute(
            'UPDATE appointment SET free = 0, name = ?, tgId = ?, username = ?, phNumber = ? WHERE date = ? AND time = ?',
            [data['name'], data['tgId'], data['username'], data['phNumber'], data['date'], data['time']]
        )
        db.commit()

# async def update_time(date, time):
#     is_free = cur.execute('SELECT free FROM appointment WHERE date = ? AND time = ?', [date, time]).fetchone()
#     if not is_free and is_free[0] == 1:
#         cur.execute('UPDATE appointment SET free = 0, name = ?, tgId = ?, telNumber = ? WHERE date = ? AND time = ?', [name, tg_id, tel_number, message, date, time])
#         db.commit()
#
# async def delete_time(data, time)
