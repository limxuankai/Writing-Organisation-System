import sqlite3, calendar
from datetime import timedelta, datetime, date
from turtle import done
from pathlib import Path
import json

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

def state_changer(counter):
    if counter > 12:
        return 2
    elif counter > 3:
        return 1
    else:
        return 0

    

class Clients():
    
    def __init__(self, name, total_commissioned, patron, wordbank, registration, counter=0):
        self.name = name
        self.total_commissioned = total_commissioned
        self.patron = patron
        self.wordbank = wordbank
        self.registration = registration
        self.counter = counter

    def save(self):
        sqlquery(
        "INSERT INTO Clients(Name, Commissioned, Patron, Word_Bank, LAST_UPDATE, Counter) VALUES (?, ?, ?, ?, ?, ?)",
        (self.name, self.total_commissioned, self.patron, self.wordbank, self.registration, self.counter))
           
    def edit(self, id):
        sqlquery(
        "UPDATE Clients SET Name = ?, Commissioned = ?, Patron = ?, Word_Bank = ?, LAST_UPDATE= ? WHERE id = ?",
        (self.name, self.total_commissioned, self.patron, self.wordbank, self.registration, id))
        
    def delete(self, id):
        sqlquery(
        "DELETE FROM Clients WHERE id = ?",
        (id,))
        
    def payrate(self):
        Cost_Per_Thousand_Words = 40
        if self.total_commissioned >= 25: 
            Cost_Per_Thousand_Words = 25
        elif self.total_commissioned >= 15:
            Cost_Per_Thousand_Words = 35
        
        patron_prices = {
            25: 25,
            20: 30,
            10: 30,
            6: 35,
            3: 35,
            0: 40
        }
        patron_rate = patron_prices[self.patron]
        return min(patron_rate, Cost_Per_Thousand_Words)
        
    def __str__(self):
        return (f"name is {self.name}, commed is {self.total_commissioned}, patron is {self.patron}, bank is {self.wordbank}")
    
    def renewal(self):
        if self.patron != 0:
            last_update = datetime.strptime(self.registration, '%Y-%m-%d')
            now = datetime.now()
            calendered_date = calendar.monthrange(now.year, now.month)
            if str(last_update.date()) != str(now.date()):
                if last_update.day <= calendered_date[1]: 
                    return now.day == last_update.day
                if last_update.day > calendered_date[1]:
                    return now.day == calendered_date[1]
            

    def incremental(self, condition, id):
        patron_increment = {
            25: [750, 750, 750],
            20: [500, 600, 600],
            10: [300, 500, 600],
            6: [250, 375, 500],
            3: [100, 250, 375]
        }

        if condition:
            self.wordbank += patron_increment[self.patron][state_changer(self.counter)]
            if self.wordbank >= 3000:
                self.wordbank = 3000
            self.registration = datetime.now().strftime('%Y-%m-%d')
            self.counter += 1
            sqlquery(
            "UPDATE Clients SET  Word_Bank = ?, LAST_UPDATE= ?, Counter = ? WHERE id = ?",
            (self.wordbank, self.registration, self.counter, id))
            
            
            
        return "Successfully Increment"
        
    
class Commission():

    def __init__(self, name, word_count, client, status="Not Started", progress = 0):
        self.name = name
        self.word_count = word_count
        self.client = client
        self.status = status
        self.progress = progress
    
    def __str__(self):
        return (f"story is {self.name}, word count is {self.word_count}, client is {self.client}, status is {self.status}, progress is {self.progress}")
    
    def save(self):
        sqlquery(
        "INSERT INTO Commission(Story, Word_Count, Client, Status, Progress) VALUES (?, ?, ?, ?, ?)",
        (self.name, self.word_count, self.client, self.status, self.progress))

    def delete(self, id):
        sqlquery(
        "DELETE FROM Commission WHERE id = ?",
        (id,))
    
    def edit(self, id):
        sqlquery(
        "UPDATE Commission SET Story = ?, Word_Count = ?, Client = ?, Status = ?, Progress= ? WHERE id = ?",
        (self.name, self.word_count, self.client, self.status, self.progress, id))


    def checkpoint(self):
        
        if self.word_count <= 3: 
            return float(self.word_count - self.progress)
        elif self.word_count < 10: 
            if self.progress >= self.word_count / 2:
                return float(self.word_count - self.progress)
            else: 
                return self.word_count/2 - self.progress
        else:
            left = self.word_count - self.progress
            return float(left % 5)
        
class Lottery():

    def __init__(self, name, total, status, written, pledge):
        self.name = name
        self.total_word_count = total
        self.status = status
        self.written_word_count = written
        self.patreon_pledge = pledge

    def __str__(self):
        return (f"Lottery Ticket: {self.name}, {self.total_word_count}, {self.written_word_count}, {self.status}, {self.patreon_pledge}")
    
    def weight(self):
        left = self.total_word_count - self.written_word_count
        if left > 10: 
            left = 10
        weight = 10 - left
        clean_name = self.name.lower()
        if "[comms]" in clean_name:
            weight += 1
        if "[own]" in clean_name:
            weight -= 2
        if self.status == "Not Started":
            weight += 2
        if "$" in clean_name:
            weight += 3
        if self.patreon_pledge == 25:
            weight *= 2
        if clean_name.find("+") != -1: 
            weight += int(clean_name[-1])
        elif clean_name.find("-") != -1: 
            weight -= int(clean_name[-1])
        
        if weight < 0:
            weight = 1
        return weight
    
    def save(self, result):
        FILE = Path("lottery.json")

        today = str(date.today())

        if FILE.exists():
            with open(FILE, "r") as f:
                data = json.load(f)

            if data["date"] == today:
                result = data["result"]
            else:
                with open(FILE, "w") as f:
                    json.dump({
                        "date": today,
                        "result": result
                    }, f)
        else:
            with open(FILE, "w") as f:
                json.dump({
                    "date": today,
                    "result": result
                }, f)

        print(result)