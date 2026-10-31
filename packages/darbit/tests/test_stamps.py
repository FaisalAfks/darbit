"""When an input happened: the time read on arrival, put right from the message's own time when it came in late."""

from darbit.platform.stamps import Stamps

MS = 1_000_000  # ns


def test_inputs_got_to_on_time_keep_the_time_read_on_arrival():
    stamps = Stamps()
    assert stamps(1000 * MS, 50) == 1000 * MS
    assert stamps(1005 * MS, 50) == 1005 * MS  # the message time ticks coarsely: arrival is finer
    assert stamps(1018 * MS, 66) == 1018 * MS
    assert stamps.late == 0


def test_inputs_got_to_late_get_their_message_time_back():
    stamps = Stamps()
    stamps(1000 * MS, 50)
    # Python was busy: inputs 50, 100 and 150 ms on are all read at once, 200 ms on
    found = [stamps(1200 * MS, 100), stamps(1200 * MS, 150), stamps(1200 * MS, 200)]
    assert found[1] - found[0] == 50 * MS  # the wait between them is back
    assert found[2] - found[1] == 50 * MS
    assert abs(found[0] - 1058 * MS) < MS  # within the message clock's tick of when it happened
    assert stamps.late == 3
    assert abs(stamps.most_late_ns - 150 * MS) < MS


def test_times_never_go_back_and_the_message_clock_can_wrap():
    stamps = Stamps()
    first = stamps(1000 * MS, 2**32 - 10)
    later = stamps(1030 * MS, 20)  # 30 ms on, the 32-bit millisecond count went round
    assert later == 1030 * MS
    assert later > first
    assert stamps(1031 * MS, 20) >= later
