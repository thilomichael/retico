"""
This module defines the abstract classes used by the incremental modules.
The AbstractModules defines some methods that handle the general tasks of a
module (like the handling of Queues).
The IncrementalQueue defines the basic functionality of an incremental queue
like appending an IU to the queue and letting modules subscribe to the Queue.
The Incremental Unit provides the basic data structure to exchange information
between modules.
"""

import queue
import threading
import time

QUEUE_TIMEOUT = 0.01

class IncrementalQueue(queue.Queue):
    """An abstract incremental queue.

    A module may subscribe to a queue of another module. Everytime a new
    incremental unit (IU) is produced, the IU is put into a special queue for
    every subscriber to the incremental queue. Every unit gets its own queue and
    may process the items at different speeds.

    Attributes:
        provider (AbstractModule): The module that provides IUs for this queue.
        consumer (AbstractModule): The module that consumes IUs for this queue.
    """

    def __init__(self, provider, consumer, maxsize=0):
        super().__init__(maxsize=maxsize)
        self.provider = provider
        self.consumer = consumer

class IncrementalUnit():
    """An abstract incremental unit.

    The IU may be used for ASR, NLU, DM, TT, TTS, ... It can be redefined to fit
    the needs of the different module (and module-types) but should always
    provide these functionalities.

    The meta_data may be used when an incremental module is having additional
    information because it is working in a simulated environemnt. This data can
    be used by later modules to keep the simulation going.

    Attributes:
        creator (AbstractModule): The module that created this IU
        previous_iu (IncrementalUnit): A link to the IU created before the
            current one.
        grounded_in (IncrementalUnit): A link to the IU this IU is based on.
        created_at (float): The UNIX timestamp of the moment the IU is created.
        meta_data (dict): Meta data that offers optional meta information. This
            field can be used to add information that is not available for all
            uses of the specific incremental unit.
    """

    def __init__(self, creator, iuid=0, previous_iu=None, grounded_in=None,
                 payload=None):
        """Initialize an abstract IU. Takes the module that created the IU as an
        argument.

        Args:
            creator (AbstractModule): The module that created this incremental
                unit.
            previous_iu (IncrementalUnit): A link to the incremental unit
                created before the current one by the same module.
            grounded_in (IncrementalUnit): A link to the incremental unit that
                this one is based on.
            payload: A generic payload that can be set.
        """
        self.creator = creator
        self.iuid = iuid
        self.previous_iu = previous_iu
        self.grounded_in = grounded_in
        self._processed_list = []
        self.payload = payload
        self.mutex = threading.Lock()

        self.meta_data = {}
        if grounded_in:
            self.meta_data = {**grounded_in.meta_data}

        self.created_at = time.time()

    def age(self):
        """Returns the age of the IU in seconds.

        Returns:
            float: The age of the IU in seconds
        """
        return time.time() - self.created_at

    def older_than(self, s):
        """Return whether the IU is older than s seconds.

        Args:
            s (float): The time in seconds to check against.

        Returns:
            bool: Whether or not the age of the IU exceeds s seconds.
        """
        return self.age() > s

    def processed_list(self):
        """Return a list of all modules that have already processed this IU.

        The returned list is a copy of the list held by the IU.

        Returns:
            list: A list of all modules that have alread processed this IU.
        """
        with self.mutex:
            return list(self._processed_list)

    def set_processed(self, module):
        """Add the module to the list of modules that have already processed
        this IU.

        Args:
            module (AbstractModule): The module that has processed this IU.
        """
        with self.mutex:
            self._processed_list.append(module)

    def __repr__(self):
        return "%s - (%s): %s" % (self.type(), self.creator.name(),
                                  str(self.payload)[0:10])

    @staticmethod
    def type():
        """Return the type of the IU in a human-readable format.

        Returns:
            str: The type of the IU in a human-readable format.
        """
        raise NotImplementedError()

class AbstractModule():
    """An abstract module that is able to incrementally process data."""

    @staticmethod
    def name():
        """Return the human-readable name of the module.

        Returns:
            str: A string containing the name of the module
        """
        raise NotImplementedError()

    @staticmethod
    def description():
        """Return the human-readable description of the module.

        Returns:
            str: A string containing the description of the module
        """
        raise NotImplementedError()

    @staticmethod
    def input_ius():
        """Return the list of IU classes that may be processed by this module.

        If an IU is passed to the module that is not in this list or a subclass
        of this list, an error is thrown when trying to process that IU.

        Returns:
            list: A list of classes that this module is able to process.
        """
        raise NotImplementedError()

    @staticmethod
    def output_iu():
        """Return the class of IU that this module is producing.

        Returns:
            class: The class of IU this module is producing.
        """
        raise NotImplementedError()

    def __init__(self, left_buffer=None, queue_class=IncrementalQueue):
        """Initialize the module with a default IncrementalQueue.

        Args:
            left_buffer (IncrementalQueue): An optioal parameter that sets the
                input queue.
            queue_class (IncrementalQueue): A queue class that should be used
                instead of the standard queue class.
        """
        self._right_buffers = []
        self.is_running = False
        self._previous_iu = False
        self._left_buffer = None
        self.mutex = threading.Lock()

        self.queue_class = queue_class

        self.iu_counter = 0

        self.set_left_buffer(left_buffer)

    def set_left_buffer(self, left_buffer):
        """Set a new left buffer for the module.

        This method stops the execution of the module pipeline if it is running.

        Args:
            left_buffer (IncrementalQueue): The new left buffer of the module.
        """
        if self.is_running:
            self.stop()
        self._left_buffer = left_buffer

    def left_buffer(self):
        """Returns the left buffer of the module.

        Returns:
            IncrementalQueue: The left buffer of the module.
        """
        return self._left_buffer

    def right_buffers(self):
        """Return the right buffers of the module.

        Note that the returned list is only a shallow copy. Modifying the list
        does not alter the internal state of the module (but modifying the
        queues in that list does).

        Returns:
            list: A list of the right buffers, each queue corresponding to an
            input of another module.
        """
        return list(self._right_buffers)

    def append(self, iu):
        """Append an IU to all queues.

        If iu is None, the method returns without doing anything.

        Args:
            iu (IncrementalUnit): The IU that should be added to all output
                queues. May be None.
        """
        if not iu:
            return
        if not isinstance(iu, IncrementalUnit):
            raise ValueError("IU is of type %s but should be IncrementalUnit" %
                             type(iu))
        for q in self._right_buffers:
            q.put(iu)

    def subscribe(self, module, q=None):
        """Subscribe a module to the queue.

        It returns a queue where the IUs for that module are placed. The queue
        is not shared with other modules. By default this method creates a new
        queue, but it may use an alternative queue given in parameter 'q'.

        Args:
            module (AbstractModule): The module that wants to subscribe to the
                output of the module.
            q (IncrementalQueue): A optional queue that is used. If q is None,
                the a new queue will be used"""
        if not q:
            q = self.queue_class(self, module)
            module.set_left_buffer(q)
        self._right_buffers.append(q)
        return q

    def unsubscribe(self, q):
        """Remove a queue from the list of queues.

        Note that this method does not take the module as an input argument,
        but rather the queue that was returned by the "subscribe" method if this
        class.

        Args:
            q (IncrementalQueue): The queue that should be deleted from the list
                of output queues"""
        self._right_buffers.remove(q)

    def unsubscribe_all(self, module):
        """Removes all queues from a given module.

        Args:
            module (AbstractModule): A module that is the consumer of one or
                more queues in the list of output queues.
        """
        new_right_buffers = []
        for q in self._right_buffers:
            if q.consumer != module:
                new_right_buffers.append(q)
        self._right_buffers.append = new_right_buffers

    def process_iu(self, input_iu):
        """Processes the information unit given and returns a new IU that can be
        appended tot the output queues.

        Note that the incremental unit that is returned should be created by the
        create_iu method so that it has correct references to the previous iu
        generated by this module and the iu that it is based on.

        It is important that the process_iu method discards iu's that are 'too
        old' so that incremental queues do not overflow.

        Args:
            input_iu (IncrementalUnit): The incremental unit that should be
                processed by the module.

        Returns:
            IncrementalUnit: The incremental unit that is produced by this
            module based on the incremental unit that was given. May be None.
        """
        raise NotImplementedError()

    def _run(self):
        self.is_running = True
        while self.is_running:
            if self._left_buffer:
                with self.mutex:
                    try:
                        input_iu = self._left_buffer.get(timeout=QUEUE_TIMEOUT)
                    except queue.Empty:
                        input_iu = None
                    if input_iu:
                        if not self.is_valid_input_iu(input_iu):
                            raise TypeError("This module can't handle this"
                                            "type of IU")
                        output_iu = self.process_iu(input_iu)
                        input_iu.set_processed(self)
                        if output_iu:
                            if (self.output_iu() is not None or
                                    isinstance(output_iu, self.output_iu())):
                                self.append(output_iu)
                            else:
                                raise TypeError("This module should not produce"
                                                " IUs of this type.")
        self.shutdown()

    def is_valid_input_iu(self, iu):
        """Return whether the given IU is a valid input IU.

        Valid is defined by the list given by the input_ius function. The given
        IU must be one of the types defined in that list or be a subclass of it.

        Args:
            iu (IncrementalUnit): The IU to be checked.

        Raises:
            TypeError: When the given object is not of type IncrementalUnit.

        Returns:
            bool: Whether the given iu is a valid one for this module.
        """
        if not isinstance(iu, IncrementalUnit):
            raise TypeError("IU is of type %s but should be IncrementalUnit" %
                            type(iu))
        for valid_iu in self.input_ius():
            if isinstance(iu, valid_iu):
                return True
        return False

    def setup(self):
        """This method is called before the module is run. This method can be
        used to set up the pipeline needed for processing the IUs."""
        pass

    def shutdown(self):
        """This method is called before the module is stopped. This method can
        be used to tear down the pipeline needed for processing the IUs."""
        pass

    def run(self, run_setup=True):
        """Run the processing pipeline of this module in a new thread. The
        thread can be stopped by calling the stop() method.

        Args:
            run_setup (bool): Whether or not the setup method should be executed
            before the thread is started.
        """
        if run_setup:
            self.setup()
        t = threading.Thread(target=self._run)
        t.start()

    def stop(self):
        """Stops the execution of the processing pipeline of this module at the
        next possible point in time. This may be after the next incoming IU is
        processed."""
        self.is_running = False

    def create_iu(self, grounded_in=None):
        """Creates a new Incremental Unit that contains the information of the
        creator (the current module), the previous IU that was created in this
        module and the iu that it is based on.

        Args:
            grounded_in (IncrementalUnit): The incremental unit that the new
                unit is based on. May be None.

        Returns:
            IncrementalUnit: A new incremental unit with correct pointer to
            unit it is grounded in and to the previous IU that was generated by
            this module.
        """
        new_iu = self.output_iu()(self, iuid=self.iu_counter,
                                  previous_iu=self._previous_iu,
                                  grounded_in=grounded_in)
        self.iu_counter += 1
        self._previous_iu = new_iu
        return new_iu

class AbstractProducingModule(AbstractModule):
    """An abstract producing module that is able to incrementally process data.

    The producing module has no input queue and thus does not wait for any
    input. The producing module is called continously and may return new output
    when it becomes available.
    """

    @staticmethod
    def name():
        raise NotImplementedError()

    @staticmethod
    def description():
        raise NotImplementedError()

    @staticmethod
    def input_ius():
        raise NotImplementedError()

    @staticmethod
    def output_iu():
        raise NotImplementedError()

    def __init__(self, queue_class=IncrementalQueue):
        super().__init__(queue_class=IncrementalQueue)

    def _run(self):
        self.is_running = True
        while self.is_running:
            with self.mutex:
                output_iu = self.process_iu(None)
                if output_iu:
                    if (self.output_iu() is not None and
                            isinstance(output_iu, self.output_iu())):
                        self.append(output_iu)
                    else:
                        raise TypeError("This module should not produce IUs of "
                                        "this type.")
    def process_iu(self, input_iu):
        raise NotImplementedError()

class AbstractConsumingModule(AbstractModule):
    """An abstract consuming module that is able to incrementally process data.

    The consuming module consumes IUs but does not return any data.
    """

    @staticmethod
    def name():
        raise NotImplementedError()

    @staticmethod
    def description():
        raise NotImplementedError()

    @staticmethod
    def input_ius():
        raise NotImplementedError()

    @staticmethod
    def output_iu():
        raise NotImplementedError()

    def subscribe(self, module, q=None):
        raise ValueError("Consuming Modules do not produce any output")

    def unsubscribe(self, q):
        raise ValueError("Consuming Modules do not produce any output")

    def unsubscribe_all(self, module):
        raise ValueError("Consuming Modules do not produce any output")

    def process_iu(self, input_iu):
        raise NotImplementedError()