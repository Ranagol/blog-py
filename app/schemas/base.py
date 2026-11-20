from pydantic import BaseModel, ConfigDict


# BaseModel is Pydantic's base class, for validation. All schemas inherit from it.
# RequestModel is a base class for request schemas, forbidding extra fields.
class RequestModel(BaseModel):
    # extra="forbid") means reject input fields the model hasn’t declared
    model_config = ConfigDict(extra="forbid")

# Author of a post or of a comment. Returned by post or comment hasOne relationship with the author.
class AuthorRead(BaseModel):
    id: int
    
    model_config = ConfigDict(from_attributes=True)