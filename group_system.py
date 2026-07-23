# Group competition storage layer
def add_score(group, amount=1):
    group["score"]=group.get("score",0)+amount
    return group["score"]
