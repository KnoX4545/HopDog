# Central permission rules
def can_use(user, action):
    if getattr(user, "in_jail", False):
        return action in {"bank","profile"}
    return True
