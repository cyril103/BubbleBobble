from enum import Enum


class GameState(str, Enum):
    TITLE = "title"
    READY = "ready"
    PLAYING = "playing"
    DYING = "dying"
    TRANSITION = "transition"
    LEVEL_CLEAR = "level_clear"
    CAMPAIGN_COMPLETE = "campaign_complete"
    GAME_OVER = "game_over"
