"""Usage limits for the public demo. Kept in memory, so they reset when the app restarts."""
import time
from collections import defaultdict, deque
from datetime import date

from . import config


class DemoLimits:
    def __init__(self):
        self.by_ip = defaultdict(deque)   # ip -> timestamps of recent messages
        self.day = date.today()
        self.today_count = 0

    def check(self, ip: str, messages_in_chat: int, now: float | None = None) -> str | None:
        """Returns a message explaining which limit was hit, or None if the request can go ahead."""
        now = now or time.time()
        if date.today() != self.day:
            self.day, self.today_count = date.today(), 0
        if self.today_count >= config.DAILY_MESSAGE_CAP:
            return "The demo has reached its daily message limit. Please try again tomorrow."
        if messages_in_chat >= config.MAX_MESSAGES_PER_CHAT:
            return (f"This chat has reached the demo limit of {config.MAX_MESSAGES_PER_CHAT} messages. "
                    "Start a new chat to keep going.")
        recent = self.by_ip[ip]
        while recent and now - recent[0] > 3600:
            recent.popleft()
        if len(recent) >= config.MAX_MESSAGES_PER_IP_PER_HOUR:
            return "You've sent a lot of messages in the last hour. Please wait a little and try again."
        recent.append(now)
        self.today_count += 1
        return None
