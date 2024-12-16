from pydantic import BaseModel
from typing import Optional
from datetime import datetime

# RESPONSE
class StatusConstant:
    GET = "Retrieved Successfully"
    GET_LIST = "Records Retrieved Successfully"
    REGISTERED = "Registered Successfully"
    CREATED = "Created Successfully"
    UPDATED = "Updated Successfully"
    DELETED = "Deleted Successfully"
    EXISTS = "Already Exists"
    ACCEPTED = "Request Accepted"
    UPLOADED = "Uploaded Successfully"
    MERGE = "Merge By Some Users, You Can't Delete!"
    NO_CONTENT = "No Record Found"
    BAD_REQUEST = "Bad Request"
    UNAUTHORIZED = "Unauthorized Access"
    FORBIDDEN = "Access Forbidden"
    NOT_FOUND = "Not Found"
    METHOD_NOT_ALLOWED = "Method Not Allowed"
    CONFLICT = "Conflict Detected"
    INTERNAL_SERVER_ERROR = "An Error Occurred"
    NOT_IMPLEMENTED = "Feature Not Implemented"
    BAD_GATEWAY = "Bad Gateway"
    SERVICE_UNAVAILABLE = "Service Unavailable"
    GATEWAY_TIMEOUT = "Gateway Timeout"
    UNSUPPORTED_MEDIA_TYPE = "Unsupported File Type"

# DTO
class RoleDTO(BaseModel):
    id: int
    name: str
    description: Optional[str] = None

    class Config:
        orm_mode = True