import socket
import time
import random
import json
import sqlalchemy
import Player as pl
import Matchmaking as Match

ServerVersion = "1"
PlayerSlots = 4
Port = 25000
serversocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
serversocket.bind((socket.gethostname(), Port))
print("Server started at " + str(socket.gethostname()) + ":" + str(Port))
Chatrooms = {"Lobby": []}
MatchRequesters = []
ActiveMatches = {}
PlayersOnServer = {}
ConnectedUsers = []
clock = time.time()
Ratios = {"XP": 100, "Credits": 200}
serversocket.setblocking(0)
sqlengine = sqlalchemy.create_engine('mssql+pyodbc://NeonDerby')
ServerRunning = False
InitialTime = time.time()

def GenerateSalt(Player):        
    Player.Salt = random.randint(1,99999999)*(time.time() - InitialTime)

def Connect(User, Pass):
    print("Connection Request From: " + User)
    try:
        sqlconn = sqlengine.connect()
        Results = sqlconn.execute('select * from Usersettings where Username = ' + User)
        row = Results.fetchone()
        sqlconn.close()
    except Exception as ex:
        print(ex)

    if str(User) == str(row['Username']) and str(Pass) == str(row['Password']):
        try:
            PlayersOnServer[address] = "Player"
            MsgStr = 'Sucessfuly connected, welcome'
            print(PlayersOnServer)
            GenerateSalt(PlayersOnServer[address])
            #CA - Connection Accepted
            msg = {"Protocol": "ca", "Data": [MsgStr, PlayersOnServer[address].Salt]}
            data = json.dumps(msg)
            serversocket.sendto(data.encode('utf-8'), address)
            msg = {"Protocol": "msg", "Data": PlayersOnServer[address].Name + " has logged in"}
            data = json.dumps(msg)
            for i in PlayersOnServer.keys():
                serversocket.sendto(data.encode('utf-8'), i)
        except Exception as ex:
            #If user cannot connect, we pop him from the virtual connection slots
            print("User could not connect, error: " + str(ex))
            PlayersOnServer[address].pop()
            print(PlayersOnServer)
    else:
        #CD - Connection Denied
        MsgStr = 'Could not connect: Invalid Username or Password'
        msg = {"Protocol": "cd", "Data": [MsgStr]}
        data = json.dumps(msg)
        serversocket.sendto(data.encode('utf-8'),address)

def Disconnect(address):
    global Chatrooms
    if PlayersOnServer[address].OnMatch == True:
        MatchID = PlayersOnServer[address].MatchID
        Player = PlayersOnServer[address].Name
        Fleet = PlayersOnServer[address].Fleet
        ActiveMatches[MatchID].Players.pop(address)
        for i in ActiveMatches[MatchID].Teams:
            if address in i:
                ActiveMatches[MatchID].Teams.pop(address)
        msg = {"Protocol": "msg", "Data": "Server: ["+Fleet+"]" + " " + Player + " Has disconnected"}
        data = json.dumps(msg)
        for i in ActiveMatches[MatchID].Players:
            serversocket.sendto(data.encode('utf-8'),i)
    else:
        Chatrooms["Lobby"].pop(address)
        
    PlayersOnServer[address].Save()
    del PlayersOnServer[address]

def CheckMessage(Received):
    # CR - Connection Request
    if Received["Protocol"] == 'cr':
        Username = Received["Data"][0]
        Password = Received["Data"][1]
        #serversocket.settimeout(0.016)
        if Received["Data"][2] != ServerVersion:
            MsgStr = 'Could not connect: Outdated Client Version'
            msg = {"Protocol": "cd", "Data": [MsgStr]}
            data = json.dumps(msg)
            serversocket.sendto(data.encode('utf-8'),address)
        elif len(PlayersOnServer) < PlayerSlots:
            print("New connection request accepted")
            Connect(Username, Password)
        else:
            MsgStr = "Could not connect: Server is full"
            msg = {"Protocol": "cd", "Data": [MsgStr]}
            serversocket.sendto(msg.encode('utf-8'), address)
            print(MsgStr)
    elif Received["Protocol"] == "cmsg":
        #serversocket.settimeout(5)
        Message = Received["Data"][0]
        Chatroom = Received["Chatroom"]
        
            #serversocket.settimeout(0.016)
        Sender = PlayersOnServer[address].Name
        Fleet = PlayersOnServer[address].Fleet
        ChatMessage = {"Protocol": "msg", "Data":"["+str(Fleet)+"]" + str(Sender) + " says: " + Message.decode()}
        data = json.dumps(ChatMessage)
        for i in Chatrooms[Chatroom]:
            serversocket.sendto(data, i)        
            
def ServerUpdate():
    global ServerTimeout
    for i in ActiveMatches:
        if i.Objective['A'] == True:
            for k in i.Teams["A"]:
                PlayersOnServer[k].WinMatch("Ship")
            for k in i.Teams["B"]:
                PlayersOnServer[k].LoseMatch("Ship")
            ActiveMatches.pop(i)
        elif i.Objective['B'] == True:
            for k in i.Teams["B"]:
                PlayersOnServer[k].WinMatch("Ship")
            for k in i.Teams["A"]:
                PlayersOnServer[k].LoseMatch("Ship")   
            ActiveMatches.pop(i)
        else:
            ActiveMatches[i].Update()
    
    for i in PlayersOnServer.keys():
        if PlayersOnServer[i].OnMatch == False:
            Chatrooms["Lobby"].add(i)
            for k in Chatrooms.keys():
                if k == "Lobby":
                    pass
                elif i in Chatrooms[k]:
                    Chatrooms[k].pop(i)
        else:
            if i in Chatrooms["Lobby"]:
                Chatrooms["Lobby"].pop(i)
            if i not in Chatrooms[PlayersOnServer[i].MatchID]:
                Chatrooms[PlayersOnServer[i].MatchID].add(i)
        
        if time.time() - PlayersOnServer[i].LastUpdate >= ServerTimeout:
            Disconnect(i)
            print(str(i) + " Has timed out from server")
        
        if PlayersOnServer[i].RequestingMatch == True:
            MatchRequesters.append(i)
            PlayersOnServer[i].RequestingMatch = False
        
    for match in ActiveMatches:
        for Player in match.Players:
            msg = {"Protocol": 'Up', "Name": PlayersOnServer[Player].Name, "Status": PlayersOnServer[Player].Status, "Position": PlayersOnServer[Player].Position, "Rotation": PlayersOnServer[Player].Rotation, "Kills": PlayersOnServer[Player].Kills, "Deaths": PlayersOnServer[Player].Deaths, "Assists": PlayersOnServer[Player].Assists, "HP": PlayersOnServer[Player].HP, "SP": PlayersOnServer[Player].SP, "Fleet": PlayersOnServer[Player].Fleet, "Team": PlayersOnServer[Player].Team}
            data = json.dumps(msg)
            for SecondaryPlayer in match.Players:
                if SecondaryPlayer != Player:
                    serversocket.sendto(data, SecondaryPlayer)
                    
    if len(MatchRequesters) >= 10:
        MatchId = len(ActiveMatches)
        ActiveMatches[MatchId] = Match.Match([],[],time.time(),MatchId,"TestMap","Team",{"A":[], "B": []},{"A": False, "B": False},[])
        for i in range(0,9):
            ActiveMatches[MatchId].Players.append(MatchRequesters[i])
            if i <= 4:
                ActiveMatches[MatchId].Teams["A"].append(MatchRequesters[i])
            else:
                ActiveMatches[MatchId].Teams["B"].append(MatchRequesters[i])
            MatchRequesters[i].pop()
            PlayersOnServer[MatchRequesters[i]].OnMatch = True                     

ServerRunning = True

while ServerRunning == True:
    try:
        #(Received, address) = serversocket.accept()
        Received, address = serversocket.recvfrom(2048)
        ReceivedPacket = json.loads(Received.decode())
        print(ReceivedPacket)
        if "Salt" in ReceivedPacket.keys():    
            Salt = ReceivedPacket["Salt"]
        elif ReceivedPacket["Protocol"] == "cr":
                CheckMessage(ReceivedPacket)
        else:
            print("Salt Conflict: " + PlayersOnServer[address].Name + " has Salt " + str(PlayersOnServer[address].Salt) + " and sender has Salt " + str(Salt))
            MsgStr = 'Disconnected from server: Security Conflict'
            msg = {"Protocol": "dc", "Data": MsgStr}
        if Salt == PlayersOnServer[address].Salt:
            CheckMessage(ReceivedPacket)
        else:
            print("Salt Conflict: " + PlayersOnServer[address].Name + " has Salt " + str(PlayersOnServer[address].Salt) + " and sender has Salt " + str(Salt))
            MsgStr = 'Disconnected from server: Security Conflict'
            msg = {"Protocol": "dc", "Data": MsgStr}
        print("PACKET FROM " + str(address) + ": " + str(Received))
    except Exception as ex:
        pass
    try:
        ServerUpdate()
    except Exception as ex:
        print(ex)
