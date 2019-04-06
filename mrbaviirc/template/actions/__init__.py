""" Provide access to all the action tags. """

__author__ = "Brian Allen Vanderburg II"
__copyright__ = "Copyright 2019"
__license__ = "Apache License 2.0"

__all__ = ["ACTION_HANDLERS"]


# Import submodules
def _import_actions():
    import pkgutil
    import importlib

    actions = {}
    for (_, name, _) in pkgutil.iter_modules(__path__):
        pkg_name = __package__ + "." + name
        module = importlib.import_module(pkg_name)

        module_actions = getattr(module, "ACTION_HANDLERS", None)
        if module_actions is None:
            continue

        for (action_name, action_handler) in module_actions.items():
            assert action_name not in actions, "Duplicate Action {0}".format(action_name)
            actions[action_name] = action_handler

    return actions


# Load them
ACTION_HANDLERS = _import_actions()
del _import_actions
