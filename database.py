import sqlite3, datetime

def sqlquery(query, params=None):
    con = sqlite3.connect('Clients.db')
    cur = con.cursor()
    
    if params:
        cur.execute(query, params)
    else:
        cur.execute(query)
        
    if "SELECT" in query.upper():  
        res = cur.fetchall()
    else:
        res = None

    con.commit()
    cur.close()  
    con.close()
    return res

#sqlquery('''CREATE TABLE Clients(id INTEGER PRIMARY KEY AUTOINCREMENT,Name TEXT,Commissioned INTEGER DEFAULT 0,Patron INTEGER DEFAULT 0,Word_Bank INTEGER DEFAULT 0
#)''')

#sqlquery('''CREATE TABLE Commission(id INTEGER PRIMARY KEY AUTOINCREMENT,Story TEXT,Word_Count INTEGER DEFAULT 0,Client TEXT,Status TEXT DEFAULT "Not Started",FOREIGN KEY (Client) REFERENCES Clients (Name) ON DELETE CASCADE ON UPDATE NO ACTION)''')
default = datetime.date(2005, 5, 18)

sqlquery(''' 
ALTER TABLE Clients ADD COLUMN Counter INTEGER DEFAULT 0;
''') 
print(sqlquery("""
SELECT name FROM sqlite_master
WHERE type='table';
"""))


