from pydantic import BaseModel, Field
from typing import Literal, Annotated, Union, Optional, cast, Any


class AddNodeArgs(BaseModel):
    nodeIP: Annotated[str, Field(description="A IPv4")]
    nodeAddress: Annotated[str, Field(description="A IP V4")]
    peerId: str
    stakerAmount: Annotated[float, Field(description="Normal integer or $ ")]


class getInfoArgs(BaseModel):
    configKey: list[str]
