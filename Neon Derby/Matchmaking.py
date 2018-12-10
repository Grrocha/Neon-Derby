import sqlalchemy
import time

class Match(object):
    
    def __init__(self, Players, Ships, Time, Id, Map, Mode, Teams, Objective, Objects):
        self.Players = Players
        self.Time = time.time()
        self.Id = Id
        self.Map = Map
        self.Teams = Teams
        self.Objective = Objective
    def Update(self):
        self.Time = time.time() - self.Time
        for i in self.Ships.keys():
            if i not in self.Players:
                del self.Ships[i]
        for i in self.Objects:
            i.Update()