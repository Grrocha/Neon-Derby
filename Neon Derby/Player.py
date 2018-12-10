import ServerRuntime as Server
import LevelProgression as Prog
import sqlalchemy
sqlengine = sqlalchemy.create_engine('mssql+pyodbc://NeonDerby')

class Player(object):
    
    def __init__(self,PID,Name,Character,Credits,Level,XP,Ships,Bonus,Booster,Inventory,OnMatch,MatchID,RequestingMatch,Status,MOTD,Position,Rotation,Salt,Kills,Deaths,Assists,TotalKills,TotalDeaths,TotalAssists, Wins, Loses, HP, SP, Fleet, LastUpdate, Team):
        self.PID = PID
        self.Name = Name
        self.Character = Character
        self.Credits = Credits
        self.Level = Level
        self.XP = XP
        self.Ships = Ships
        self.Bonus = Bonus
        self.Booster = Booster
        self.Inventory = Inventory
        self.OnMatch = OnMatch
        self.MatchID = MatchID
        self.RequestingMatch = RequestingMatch
        self.Status = Status
        self.MOTD = MOTD
        self.Position = Position
        self.Rotation = Rotation
        self.Salt = Salt
        self.Kills = Kills
        self.Deaths = Deaths
        self.Assists = Assists
        self.TotalKills = TotalKills
        self.TotalDeaths = TotalDeaths
        self.TotalAssists = TotalAssists
        self.Wins = Wins
        self.Loses = Loses
        self.HP = HP
        self.SP = SP
        self.Fleet = Fleet
        self.LastUpdate = LastUpdate
        self.Team = Team
    
    def Update(self):
        if self.XP >= Prog.CalcXP(self.Level):
            self.XP -= Prog.CalcXP(self.Level)
            self.Level += 1
            self.OnMatch = False
            self.MatchID = -1
            
    def WinMatch(self,Ship):
        self.Wins += 1
        self.TotalKills += self.Kills
        self.TotalDeaths += self.Deaths
        self.TotalAssists += self.Assists
        self.XP += ((self.Kills/self.Deaths + (self.Assists/2)/self.Deaths)*Server.Ratios['XP'])* self.Booster
        self.Credits += ((self.Kills/self.Deaths + (self.Assists/2)/self.Deaths)*Server.Ratios['Credits'])* self.Booster
        self.Kills = 0
        self.Deaths = 0
        self.Assists = 0
        self.Update()
    
    def LoseMatch(self,Ship):
        self.Loses += 1
        self.TotalKills += self.Kills
        self.TotalDeaths += self.Deaths
        self.TotalAssists += self.Assists
        self.XP += ((self.Kills/self.Deaths + (self.Assists/2)/self.Deaths)*Server.Ratios['XP']/2)* self.Booster
        self.Credits += 100 + (self.Kills/self.Deaths + (self.Assists/2)/self.Deaths)*Server.Ratios['Credits']/5
        self.Kills = 0
        self.Deaths = 0
        self.Assists = 0
        self.Update()
        
    def Save(self):
        SaveString = "Credits = " + str(self.Credits) + ", Level = " + str(self.Level) + ", XP = " + str(self.XP) + ", Booster = " + str(self.Booster) + ", MOTD = " + str(self.MOTD) + ", TotalKills = " + str(self.TotalKills) + ", TotalDeaths = " + str(self.TotalDeaths) + ", TotalAssists = " + str(self.TotalAssists) + ", Fleet = " + str(self.Fleet)
        global sqlengine
        try:
            sqlconn = sqlengine.connect()
            sqlconn.execute('Update Usersettings set ' + SaveString + ' where PID = ' + self.PID)
            sqlconn.close()
        except Exception as ex:
            print(ex)
        