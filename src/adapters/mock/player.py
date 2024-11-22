import dataclasses
import re
import time

from src.domain.player import Action, Playback, PlaybackFactory


class PrintAction(Action):
    def __init__(self, text):
        self.text = text

    def execute(self):
        print(self.text)


class SilenceAction(Action):
    def __init__(self, ms: int):
        self.ms = ms

    def execute(self):
        time.sleep(self.ms / 1000)


@dataclasses.dataclass
class ActionTimeline:
    start: int
    duration: int
    action: Action


class TextPlaybackBuilder(PlaybackFactory):
    def create_playback(self, payload: bytes) -> Playback:
        action_timelines = []
        actions = []
        cursor = 0
        for command in payload.split(b'&'):
            timestamp, text = command.split(b':', maxsplit=1)
            action = PrintAction(text=str(text))
            action_timeline = ActionTimeline(
                start=int(timestamp),
                duration=0,
                action=action
            )
            action_timelines.append(action_timeline)

        for action_timeline in sorted(action_timelines, key=lambda x: x.start):
            start = action_timeline.start
            silence_duration = start - cursor
            if silence_duration:
                silence_action = SilenceAction(ms=silence_duration)
                actions.append(silence_action)
            actions.append(action_timeline.action)
            cursor = start + action_timeline.duration
        return Playback(actions=actions)
