from flask import Flask, render_template, redirect, request, url_for, abort
from Forms import CreateClientForm, UpdateClientForm, CreateCommissionsForm, UpdateCommissionsForm
from Setup import sqlquery, Clients, Commission, Lottery
import datetime
import random as re 
import json
from pathlib import Path

app = Flask(__name__)


@app.route("/")
def home():
    Comms_Info = sqlquery("SELECT * FROM COMMISSION INNER JOIN Clients ON Clients.Name = Commission.Client;")
    Comms_List = [i for i in Comms_Info]
    In_Progress = sqlquery("SELECT COUNT(*) FROM COMMISSION INNER JOIN Clients ON Clients.Name = Commission.Client WHERE COMMISSION.Status = 'In Progress'")
    Not_Started = sqlquery("SELECT COUNT(*) FROM COMMISSION INNER JOIN Clients ON Clients.Name = Commission.Client WHERE COMMISSION.Status = 'Not Started'")
    On_Hold = sqlquery("SELECT COUNT(*) FROM COMMISSION INNER JOIN Clients ON Clients.Name = Commission.Client WHERE COMMISSION.Status = 'On Hold'")

    Patron_Clients = sqlquery("SELECT * FROM Clients WHERE Patron != 0")

    with open("lottery.json", "r") as f:
        data = json.load(f)
    if data["date"] == str(datetime.date.today()):
        result = data["result"]
    else: 
        result = "Roll for it!"
    for i in Patron_Clients:
        Viewing_Client = Clients(i[1], i[2], i[3], i[4], i[5], i[6])
        Viewing_Client.incremental(Viewing_Client.renewal(), i[0])

    return render_template("home.html", Comms = Comms_List, Progress = In_Progress[0][0], UnStart = Not_Started[0][0], Hold = On_Hold[0][0], chosen = result)


@app.route('/create', methods=['GET', 'POST'])
def create():
    Client_Data = CreateClientForm(request.form)

    if request.method == 'POST' and Client_Data.validate():
        if Client_Data.Registered.data == datetime.date(2005, 5, 18):
            Client_Data.Registered.data = None

        Client = Clients(Client_Data.Name.data, 0, Client_Data.Patron.data, Client_Data.Word_Bank.data, Client_Data.Registered.data)
        Client.save()   
        return redirect(url_for('view'))
    return render_template('createclient.html', form=Client_Data)


@app.route('/view')
def view():
    List_Clients = sqlquery("SELECT * FROM Clients")
    Client_List = [i for i in List_Clients]
    Total_Patron = sqlquery("SELECT SUM(Patron) FROM Clients")
    return render_template('clientoverview.html', client_list = Client_List, patron = Total_Patron)


@app.route('/view/<int:id>')
def view_personal(id):
    Client = sqlquery("SELECT * FROM Clients WHERE id = ?", (id,))
    print(Client)
    Viewing_Client = Clients(Client[0][1], Client[0][2], Client[0][3], Client[0][4], Client[0][5], Client[0][6])
    payrate = Viewing_Client.payrate()
    Client_Details = [i for i in Client]
    return render_template('clientindividual.html', client = Client_Details, Payrate = payrate)


@app.route('/update/<int:id>', methods=["POST", "GET"])
def update(id):
    Changed_Data = UpdateClientForm(request.form)
    if request.method == 'POST':
        Client = sqlquery("SELECT * FROM Clients WHERE id = ?", (id,))
        Editting_Client = Clients(Client[0][1], Client[0][2], Client[0][3], Client[0][4], Client[0][5])

        if Changed_Data.Name.data != "": 
            Editting_Client.name = Changed_Data.Name.data

        if Changed_Data.Total_Commissioned.data is not None:
            Editting_Client.total_commissioned = Changed_Data.Total_Commissioned.data

        if Changed_Data.Patron.data is not None:
            Editting_Client.patron = Changed_Data.Patron.data

        if Changed_Data.Word_Bank.data is not None:
            Editting_Client.wordbank = Changed_Data.Word_Bank.data
        
        if Changed_Data.Registered.data is not None: 
            Editting_Client.registration = Changed_Data.Registered.data

        Editting_Client.edit(id)

        return redirect(url_for('view'))
    else:
        return render_template('editclient.html', form = Changed_Data)


@app.route('/delete/<int:id>/', methods = ["POST"])
def delete(id):
    Client = sqlquery("SELECT * FROM Clients WHERE id = ?", (id,))
    Deleting_Client = Clients(Client[0][1], Client[0][2], Client[0][3], Client[0][4], Client[0][5])
    Deleting_Client.delete(id)
    return redirect(url_for('view'))


@app.route('/commscreate', methods=['GET', 'POST'])
def comms_create():
    Comms_Data = CreateCommissionsForm(request.form)
    Client_List = sqlquery("SELECT Name from Clients")
    New_Client_List = []
    for i in range(len(Client_List)):
            New_Client_List += Client_List[i]

    Comms_Data.Name.choices = New_Client_List

    if request.method == 'POST' and Comms_Data.validate():
            New_Commission = Commission(Comms_Data.Story.data, Comms_Data.Word_Count.data, Comms_Data.Name.data)
            New_Commission.save()
            print("Form POST received")
            return redirect(url_for('comms_queue'))
        
    return render_template('createcomms.html', form=Comms_Data)


@app.route('/comms')
def comms_queue():
    Comms_Info = sqlquery("SELECT * FROM COMMISSION INNER JOIN Clients ON Clients.Name = Commission.Client;")
    Comms_List = [i for i in Comms_Info]
    return render_template('commsoverview.html', Comms = Comms_List)


@app.route('/viewcomms/<int:id>/')
def comms_invid(id):
    Comms_Info = sqlquery("SELECT * FROM COMMISSION INNER JOIN Clients ON Clients.Name = Commission.Client WHERE Commission.id = ?", (id,))
    Comms_List = [i for i in Comms_Info]
    Client = Clients(Comms_List[0][7], Comms_List[0][8], Comms_List[0][9], Comms_List[0][10], Comms_List[0][11])
    Progress = int(Comms_List[0][5]) / int(Comms_List[0][2]) * 100
    Earnable_Amount = Client.payrate() * Comms_List[0][2]
    Commmsissioned = Commission(Comms_List[0][1], Comms_List[0][2], Comms_List[0][3], Comms_List[0][4], Comms_List[0][5])
    Checkpoint = Commmsissioned.checkpoint()
    return render_template('commsindividual.html', Comms = Comms_List, Pay = Earnable_Amount, Checkpoint = Checkpoint, Progress = Progress)


@app.route('/updatecomms/<int:id>/', methods=['GET', 'POST'])
def update_comms(id):
    Changed_Data = UpdateCommissionsForm(request.form)
    Client_List = sqlquery("SELECT Name from Clients")
    New_Client_List = []
    for i in range(len(Client_List)):
            New_Client_List += Client_List[i]

    New_Client_List.append("")
    Changed_Data.Name.choices = New_Client_List
    Changed_Data.Status.choices = [" ","Not Started", "In Progress", "Cancelled", "On Hold"]
    if request.method == 'POST':
        Comm = sqlquery("SELECT * FROM Commission WHERE id = ?", (id,))
        Editting_Comms = Commission(Comm[0][1], Comm[0][2], Comm[0][3], Comm[0][4], Comm[0][5])

        if Changed_Data.Story.data != "": 
            Editting_Comms.name = Changed_Data.Story.data

        if Changed_Data.Name.data != "":
            Editting_Comms.client= Changed_Data.Name.data

        if Changed_Data.Word_Count.data != 0:
            Editting_Comms.word_count= Changed_Data.Word_Count.data
        
        if Changed_Data.Progress.data is not None: 
            Editting_Comms.progress = Changed_Data.Progress.data
        
        if Changed_Data.Status.data != " ":
            Editting_Comms.status = Changed_Data.Status.data

        if Editting_Comms.progress == Editting_Comms.word_count: 
            Editting_Comms.delete(id)
        
        if Editting_Comms.status == "Cancelled": 
            Editting_Comms.delete(id)

        Editting_Comms.edit(id)

        return redirect(url_for('comms_queue'))
    else:
        return render_template('updatecomms.html', form = Changed_Data)


@app.route('/progress/<int:id>/', methods=["GET", "POST"])
def progress(id):
    Comms = sqlquery("SELECT * FROM Commission WHERE id = ?", (id,))
    Client = sqlquery("SELECT Clients.id, Name, Commissioned, Patron, Word_Bank, LAST_UPDATE FROM COMMISSION RIGHT JOIN Clients ON Clients.Name = Commission.Client WHERE Commission.id = ?", (id,))
    Commissioner = Clients(Client[0][1], Client[0][2], Client[0][3], Client[0][4], Client[0][5])
    Worked_Comms = Commission(Comms[0][1], Comms[0][2], Comms[0][3], Comms[0][4], Comms[0][5])

    New_Progress = request.form.get("progress", type=int)
    Progress = New_Progress - Worked_Comms.progress
    Worked_Comms.progress = New_Progress

    if Worked_Comms.progress == Worked_Comms.word_count:
        Worked_Comms.delete(id)
    elif Worked_Comms.status == "Not Started" and Worked_Comms.progress > 0: 
        Worked_Comms.status = "In Progress"

    Commissioner.total_commissioned += Progress
    Commissioner.edit(Client[0][0])
    Worked_Comms.edit(id)
    
    return redirect(url_for('comms_queue'))


@app.route('/deletecomms/<int:id>/', methods = ["POST"])
def comms_delete(id):
    Comms = sqlquery("SELECT * FROM Commission WHERE id = ?", (id,))
    Deleting_Comms = Commission(Comms[0][1], Comms[0][2], Comms[0][3], Comms[0][4], Comms[0][5])
    Deleting_Comms.delete(id)
    return redirect(url_for('comms_queue'))

@app.route('/work')
def work():
    Comms_Info = sqlquery("SELECT * FROM COMMISSION INNER JOIN Clients ON Clients.Name = Commission.Client WHERE COMMISSION.Status = 'In Progress' OR COMMISSION.Status = 'Not Started';")
    Comms_List = [i for i in Comms_Info]
    In_Progress = sqlquery("SELECT COUNT(*) FROM COMMISSION INNER JOIN Clients ON Clients.Name = Commission.Client WHERE COMMISSION.Status = 'In Progress'")
    Not_Started = sqlquery("SELECT COUNT(*) FROM COMMISSION INNER JOIN Clients ON Clients.Name = Commission.Client WHERE COMMISSION.Status = 'Not Started'")
    with open("lottery.json", "r") as f:
        data = json.load(f)
    
    if data["date"] == str(datetime.date.today()):
        result = data["result"]
    else:
        Tickets = []
        for i in range(len(Comms_Info)):
                Lottery_Ticket = Lottery(Comms_Info[i][1], Comms_Info[i][2],Comms_Info[i][4], Comms_Info[i][5], Comms_Info[i][9])
                
                for o in range(Lottery_Ticket.weight()):
                    Tickets.append(Lottery_Ticket)
        re.shuffle(Tickets)
        FILE = Path("./lottery.json")
        today = str(datetime.date.today())
        result = []
        for i in Tickets:
            if len(Tickets) > 0 and len(result) < 10:
                result.append(i.name)
                Tickets.remove(i)
        if FILE.is_file():
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


    return render_template('work.html', chosen = result,  Comms = Comms_List, Progress = In_Progress[0][0], UnStart = Not_Started[0][0])

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

if  __name__ == "__main__":
    app.run(debug=True)
