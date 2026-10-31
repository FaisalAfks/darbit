"""When an input really happened, for the recorder's listener (decision 0014).

The listener can only read the clock when it gets to an input, and Python sometimes gets there late (another
thread had a turn): a run of inputs then all read the same moment, and the waits between them are lost. Windows
also keeps the time each input message was sent (GetMessageTime: milliseconds, though it only ticks every 10 to
16 ms). Normally the clock read on arrival is the better one; when that is clearly later than the message's own
time, the message's time is used.

    stamps = Stamps()
    time_ns = stamps(time.perf_counter_ns(), user32.GetMessageTime())
"""

TICK_NS = 16_000_000  # GetMessageTime moves on about every 15.6 ms
LATE_NS = 20_000_000  # later than this after the message's time, and we were late getting to it
DRIFT = 200e-6  # the two clocks can drift apart by about this share of the time gone by
WRAP = 1 << 32  # GetMessageTime counts milliseconds in 32 bits


class Stamps:
    """Turn (time read on arrival, the message's own time) into when the input happened, in perf_counter ns."""

    def __init__(self) -> None:
        self.first_tick: int | None = None
        self.base: int | None = None  # perf_counter ns at message time 0, from the least late message seen
        self.base_at = 0  # when base was last set
        self.last = 0  # never go back in time
        self.late = 0  # inputs that came in late, and had their time put right
        self.most_late_ns = 0

    def __call__(self, now_ns: int, tick_ms: int) -> int:
        if self.first_tick is None:
            self.first_tick = tick_ms
        sent_ns = ((tick_ms - self.first_tick) % WRAP) * 1_000_000
        offset = now_ns - sent_ns
        if self.base is None:
            self.base = offset
            self.base_at = now_ns
        else:
            allowed = self.base + int((now_ns - self.base_at) * DRIFT)  # the clocks may have drifted since
            self.base = min(offset, allowed)
            self.base_at = now_ns
        earliest = self.base + sent_ns  # the input happened at or after this, and within TICK_NS of it
        stamp = now_ns
        behind = now_ns - earliest
        if behind > LATE_NS:
            stamp = earliest + TICK_NS // 2
            self.late += 1
            self.most_late_ns = max(self.most_late_ns, behind)
        stamp = max(stamp, self.last)
        self.last = stamp
        return stamp
