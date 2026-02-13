"""Instance manager: Windows named mutex only.

API:
- InstanceManager(mutex_name='KS_SnapClip_Mutex')
- acquire() -> bool (True if primary)
- release()
"""

import logging


class InstanceManager:
    def __init__(self, mutex_name: str = "KS_SnapClip_Mutex"):
        self.mutex_name = mutex_name
        self._is_primary = False
        self._mutex = None

    def acquire(self) -> bool:
        try:
            import win32event
            import win32api
            try:
                import win32con
            except Exception:
                win32con = None
            # CreateMutex returns a handle; if it already existed, GetLastError will be ERROR_ALREADY_EXISTS
            self._mutex = win32event.CreateMutex(None, False, self.mutex_name)
            err = win32api.GetLastError()
            # ERROR_ALREADY_EXISTS numeric value
            ERROR_ALREADY_EXISTS = 183
            if win32con is not None and hasattr(win32con, 'ERROR_ALREADY_EXISTS'):
                if err == win32con.ERROR_ALREADY_EXISTS:
                    self._is_primary = False
                else:
                    self._is_primary = True
            else:
                # fallback numeric compare
                if err == ERROR_ALREADY_EXISTS:
                    self._is_primary = False
                else:
                    self._is_primary = True
            return self._is_primary
        except Exception:
            # If win32 APIs are not available or something unexpected happened, conservatively assume primary
            logging.exception('win32mutex acquire failed; assuming primary')
            self._is_primary = True
            return True

    def release(self):
        try:
            import win32api
            if self._mutex:
                win32api.CloseHandle(self._mutex)
                self._mutex = None
        except Exception:
            pass


# convenience functions
_default_manager = None

def acquire_instance():
    global _default_manager
    _default_manager = InstanceManager()
    return _default_manager.acquire()


def release_instance():
    if _default_manager is None:
        return
    _default_manager.release()