from datetime import datetime
from pydantic import BaseModel, Field
class Candle(BaseModel):
 timestamp: datetime
 open: float
 high: float
 low: float
 close: float
 volume: int = Field(ge=0)
class PaperTradeRequest(BaseModel):
 symbol: str
 side: str
 quantity: int = Field(gt=0,le=100000)
 reference_price: float = Field(gt=0)
class PaperTrade(BaseModel):
 id: str
 symbol: str
 side: str
 quantity: int
 entry_price: float
 status: str
 created_at: datetime
