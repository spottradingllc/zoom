class ApplicationStatus():
    RUNNING = 1
    STARTING = 2
    STOPPED = 3

class UpdateType():
    APPLICATION_STATE_UPDATE = "application_state"
    GLOBAL_MODE_UPDATE = "global_mode"