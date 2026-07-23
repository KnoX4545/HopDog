# Leaderboard calculations
def sort_groups(groups):
    return sorted(groups,key=lambda x:x.get("score",0),reverse=True)
