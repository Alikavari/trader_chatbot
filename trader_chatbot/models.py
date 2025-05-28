from sqlmodel import SQLModel, Field

class WalletUsage(SQLModel, table=True):
    user_wallet_address: str = Field(primary_key=True)
    token_usage: int = Field(default=0)