def unchecked_total(connection):
    return connection.execute('SELECT SUM(p.units) FROM production p JOIN devices d ON p.device=d.device').fetchone()[0]
