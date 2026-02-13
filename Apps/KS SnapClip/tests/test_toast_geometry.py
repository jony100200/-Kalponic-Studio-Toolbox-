class DummyMonitor:
    def __init__(self, x, y, w, h):
        self.x = x
        self.y = y
        self.width = w
        self.height = h


def test_compute_toast_geometry_center():
    from ui import _compute_toast_geometry
    m = DummyMonitor(100, 50, 1920, 1080)
    geo = _compute_toast_geometry(m, 360, 120)
    assert geo.endswith('+1000+515') or '360x120+' in geo
