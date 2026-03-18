"""
CamelModel: project-wide Pydantic base class.

alias_generator=to_camel   — snake_case Python field names automatically get a
                              camelCase alias for the JSON wire format.
                              Already-camelCase names (phoneNumber, oldPin, hasPIN)
                              are unaffected — to_camel is a no-op when there are
                              no underscores in the name.
populate_by_name=True      — constructors and parsers accept both the Python
                              field name and the camelCase alias; existing
                              model_validator code that accesses self.field_name
                              continues to work without change.

All request and response schemas inherit from CamelModel instead of BaseModel.
Individual schemas may still override extra="forbid" or from_attributes as needed;
Pydantic v2 merges child model_config with the parent's settings.
"""
from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class CamelModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )
