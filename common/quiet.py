import os


def quiet_enabled():
    v = os.environ.get("DISTRIBUTED_QUIET", "")
    return v.strip().lower() in {"1", "true", "yes", "on"}


def dprint(*args, **kwargs):
    if not quiet_enabled():
        print(*args, **kwargs)
