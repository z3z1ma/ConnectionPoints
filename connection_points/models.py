from datetime import datetime

from pynamodb.attributes import (
    BinaryAttribute,
    BooleanAttribute,
    ListAttribute,
    NumberAttribute,
    UnicodeAttribute,
    UTCDateTimeAttribute,
)
from pynamodb.indexes import AllProjection, LocalSecondaryIndex
from pynamodb.models import Model


class Challenge(Model):
    class Meta:
        table_name = "connection-points-challenges"
        region = "us-west-1"

    partyId = UnicodeAttribute(range_key=True)  # Lookup

    name = UnicodeAttribute()  # Lookup
    description = UnicodeAttribute()
    points = NumberAttribute()
    creator = UnicodeAttribute()
    createDate = UTCDateTimeAttribute(default=datetime.now)
    dueDate = UTCDateTimeAttribute()
    recurring = UnicodeAttribute()  # Enum: daily, weekly, monthly, yearly

    owner = UnicodeAttribute()
    status = UnicodeAttribute()
    updateDate = UTCDateTimeAttribute()

    completeDate = UTCDateTimeAttribute()
    accepted = BooleanAttribute()
    credited = BooleanAttribute()
    picture = BinaryAttribute()
    id = UnicodeAttribute(hash_key=True)


class Reward(Model):
    class Meta:
        table_name = "connection-points-rewards"
        region = "us-west-1"

    partyId = UnicodeAttribute(range_key=True)  # Lookup

    name = UnicodeAttribute()  # Lookup
    description = UnicodeAttribute()
    cost = NumberAttribute()
    creator = UnicodeAttribute()
    createDate = UTCDateTimeAttribute(default=datetime.now)

    recurring = UnicodeAttribute(null=True)  # Enum: daily, weekly, monthly, yearly

    recipient = UnicodeAttribute()
    status = UnicodeAttribute(default="unclaimed")
    updateDate = UTCDateTimeAttribute()

    id = UnicodeAttribute(hash_key=True)
    accepted = BooleanAttribute(default=False)


class Party(Model):
    class Meta:
        table_name = "connection-points-parties"
        region = "us-west-1"

    name = UnicodeAttribute(hash_key=True)
    description = UnicodeAttribute()
    createDate = UTCDateTimeAttribute()
    owner = UnicodeAttribute()
    status = UnicodeAttribute()
    updatedate = UTCDateTimeAttribute()

    id = UnicodeAttribute()
    inviteKey = UnicodeAttribute()


class EmailNameIndex(LocalSecondaryIndex):
    class Meta:
        projection = AllProjection()

    email = UnicodeAttribute(hash_key=True)
    name = UnicodeAttribute(range_key=True)


class User(Model):
    class Meta:
        table_name = "connection-points-users"
        region = "us-west-1"

    email = UnicodeAttribute(hash_key=True)
    name_index = EmailNameIndex()
    name = UnicodeAttribute(range_key=True)
    displayName = UnicodeAttribute()
    createDate = UTCDateTimeAttribute(default=datetime.now)
    password = UnicodeAttribute()

    parties = ListAttribute()


class AuthConfig(Model):
    class Meta:
        table_name = "connection-points-auth"
        region = "us-west-1"

    COOKIE_NAME = "connection-points-cookie"

    expiry_days = NumberAttribute(default=30)
    key = UnicodeAttribute()
    name = UnicodeAttribute(hash_key=True, default=COOKIE_NAME)


BaseModel = Model

__all__ = ["Challenge", "Reward", "Party", "User", "AuthConfig", "BaseModel"]
