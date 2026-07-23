# Upgrade prices are centralized here
import config
def upgrade_price(level):
    return getattr(config,"UPGRADE_PRICES",{}).get(level+1)
