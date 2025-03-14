class Animation:
    def __init__(self, frames: list[str], flipped: list[str] | None, fps: int):
        self.frames = frames
        self.flipped = flipped
        self.is_flipped = False
        self.fps = fps
        self.frame = 0.0

    @property
    def current(self):
        buff = self.frames if not self.is_flipped else self.flipped
        return buff[int(self.frame)]

    def flip(self, flip=True):
        self.is_flipped = flip
        return self

    def run(self, dt: float):
        self.frame = (self.frame + dt*self.fps) % len(self.frames)
        return self.current

    def reset(self):
        self.frame = 0.0
        return self


class vec2:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    @property
    def xy(self):
        return self.x, self.y
