from instance import InstanceManager


def test_mutex_single_instance():
    m1 = InstanceManager()
    ok1 = m1.acquire()
    assert isinstance(ok1, bool)

    m2 = InstanceManager()
    ok2 = m2.acquire()
    # both cannot be primary at the same time
    assert not (ok1 and ok2)

    # cleanup if we own the mutex
    if ok1:
        m1.release()
