from client.match.countdown import Countdown


def test_countdown_counts_down_to_zero() -> None:
    countdown = Countdown(duration=3.0)
    assert countdown.active
    assert countdown.label == "3"

    countdown.update(1.2)
    assert countdown.active
    assert countdown.label == "2"

    countdown.update(5.0)
    assert not countdown.active
    assert countdown.label == ""


def test_countdown_reset_restores_duration() -> None:
    countdown = Countdown(duration=2.0)
    countdown.update(2.0)
    countdown.reset()
    assert countdown.active
    assert countdown.label == "2"

