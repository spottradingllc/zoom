class ApplicationStatus():
    RUNNING = 1
    STARTING = 2
    STOPPED = 3


class CommandType():
    CANCEL = "cancel"


class UpdateType():
    APPLICATION_STATE_UPDATE = "application_state"
    APPLICATION_DEPENDENCY_UPDATE = "application_dependency"
    GLOBAL_MODE_UPDATE = "global_mode"
    TIMING_UPDATE = "timing_estimate"


class OperationType():
    ADD = 'add'
    REMOVE = 'remove'
