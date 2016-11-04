""" Provide a very basic signals-and-slots feature. """

__author__      = "Brian Allen Vanderburg II"
__copyright__   = "Copyright 2016"
__license__     = "Apache License 2.0"


import weakref


# A slot for a strong reference
class _Slot(object):
    def __init__(self, fn):
        self.__fn = fn

    def execute(self, *args, **kwargs):
        result = self.__fn(*args, **kwargs)
        return (True, result)

    def getid(self):
        return id(self)


# A slot for a weak reference connection, one that will automatically
# disconnect when the target is gone.
class _WeakSlot(object):
    def __init__(self, signal, fn):
        self.__signal = weakref.ref(signal)
        if hasattr(fn, 'im_self'):
            # for normal method im_self is instance
            # for class method im_self is class instance
            self.__obj = weakref.ref(fn.im_self, self.cleanup)
            self.__fn = weakref.ref(fn.im_func, self.cleanup)
        else:
            # function and static methods are only a function objects
            self.__obj = None
            self.__fn = weakref.ref(fn, self.cleanup)

    def execute(self, *args, **kwargs):
        obj = None
        if self.__obj is not None:
            obj = self.__obj()
            if obj is None:
                return (False, None)

        fn = self.__fn()
        if fn is None:
            return (False, None)

        if obj:
            result = fn(obj, *args, **kwargs)
        else:
            result = fn(*args, **kwargs)

        return (True, result)

    def cleanup(self, ref):
        signal = self.__signal()
        if signal is not None:
            signal.disconnect(self.getid())

    def getid(self):
        return id(self)


# The signal object
class Signal(object):
    """A signal that can connect to and call slots.
    """

    class Combiner(object):
        """Combine return values from slots.

        By default the result of a signal is the value of the last
        slot called.  To create a custom combiner, derive a custom
        signal class and in it a custom Combiner class.  The custom
        combiner class must implement combine and finalize.
        """

        def __init__(self):
            self.__value = None

        def combine(self, value):
            """Combine the return value of a slot.

            Return True to continue processing slots or False to stop.
            """

            self.__value = value
            return True

        def finalize(self):
            """Get the final value.

            Return the final value of the combined values
            """

            return self.__value

    def __init__(self):
        """Initialize the signal to an empty slot list
        """

        self.__slots = [ ]

    def connect(self, fn, weak=True):
        """Connect a signal to a slot.

        If a weak connection is made, the connection will be disconnect
        automatically when the target is removed.  The function be a
        callable with 'im_self' and 'im_func' attributes.

        If a strong connection is make, the function must be callable
        but does not automatically disconnect.  The function can not
        be deleted until it is disconnected.

        Returns the connection id for later disconnecting.
        """

        if weak:
            slot = _WeakSlot(self, fn)
        else:
            slot = _Slot(fn)

        self.__slots.append(slot)

        return slot.getid()

    def disconnect(self, id):
        """Disconnect a slot.

        Disconnect a slot that was connected.  If the connection does
        not exist, it will not be disconnected.
        """

        for i in xrange(len(self.__slots)):
            if self.__slots[i].getid() == id:
                del self.__slots[i]
                break

    def disconnectAll(self):
        """Disconnect all slots.
        """

        self.__slots = [ ]

    def __call__(self, *args, **kwargs):
        """Call all slots.

        Each slot is called in the order that it was added.  Then the
        return value is passed to the combiner by calling its combine
        method.  If combine returns False no more slots are called.
        When finished, the finalize method of the combiner is called
        and the result is returned.
        """

        combiner = self.Combiner()
        for i in xrange(len(self.__slots)):
            (called, result) = self.__slots[i].execute(*args, **kwargs)
            if called and combiner.combine(result) == False:
                break
        return combiner.finalize()


