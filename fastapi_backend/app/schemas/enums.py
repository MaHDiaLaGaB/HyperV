from enum import StrEnum


class ClientType(StrEnum):
    OIL_GAS = "oil_gas"
    DEFENCE = "defence"
    INTERIOR = "interior"
    ENVIRONMENT = "environment"
    SYSTEM = "system"
    OTHER = "other"


class AssetType(StrEnum):
    IMAGE = "image"
    VIDEO = "video"
    GIS = "gis"


class EventType(StrEnum):
    LEAK = "leak"
    BREACH = "breach"
    DRONE_FLY = "drone_fly"
    FALSE_ALERT = "false_alert"
    FIRE = "fire"
    DEFORESTATION = "deforestation"
    OTHER = "other"


class ReportFrequency(StrEnum):
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
