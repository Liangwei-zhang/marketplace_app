from enum import Enum


class ItemCategory(str, Enum):
    ELECTRONICS = "electronics"
    CLOTHING = "clothing"
    FURNITURE = "furniture"
    BOOKS = "books"
    SPORTS = "sports"
    GAMES = "games"
    OTHER = "other"

    @classmethod
    def choices(cls):
        return [c.value for c in cls]


# Product status
ITEM_STATUS_AVAILABLE = 0
ITEM_STATUS_RESERVED = 1  # 有人想要，聊天中
ITEM_STATUS_SOLD = 2

# Max images per item
MAX_ITEM_IMAGES = 9
ALLOWED_IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB
