import ServerRuntime as Server
def CalcXP(level):
    if level > 1:
        return Server.Ratios*(level + level/2) + 500
    else:
        return 500