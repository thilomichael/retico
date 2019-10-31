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

    A module may subscribe to a queue of another module. Every time a new
    incremental unit (IU) is produced, the IU is put into a special queue for
    every subscriber to the incremental queue. Every unit gets its own queue and
    may process the items at different speeds.

    Attributes:
        provider (AbstractModule): The module that provides IUs for this queue.
        consumer (AbstractModule): The module that consumes IUs for this queue.
        maxsize (int): The maximum size of the queue, where 0 does not restrict
            the size.
    """

    def __init__(self, provider, consumer, maxsize=0):
        super().__init__(maxsize=maxsize)
        self.provider = provider
        self.consumer = consumer

    def remove(self):
        """Removes the queue from the consumer and the producer."""
        self.provider.remove_right_buffer(self)
        self.consumer.remove_left_buffer(self)


class IncrementalUnit:
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

    MAX_DEPTH = 10

    def __init__(
        self,
        creator=None,
        iuid=0,
        previous_iu=None,
        grounded_in=None,
        payload=None,
        **kwargs
    ):
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

        self.committed = False
        self.revoked = False

        self.meta_data = {}
        if grounded_in:
            self.meta_data = {**grounded_in.meta_data}

        self.created_at = time.time()
        self._remove_old_links()

    def _remove_old_links(self):
        current_depth = 0
        previous_iu = self.previous_iu
        while previous_iu:
            if current_depth == self.MAX_DEPTH:
                previous_iu.previous_iu = None
            previous_iu = previous_iu.previous_iu
            current_depth += 1
        current_depth = 0
        grounded_in = self.grounded_in
        while grounded_in:
            if current_depth == self.MAX_DEPTH:
                grounded_in.grounded_in = None
            grounded_in = grounded_in.grounded_in
            current_depth += 1

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
        if not isinstance(module, AbstractModule):
            raise TypeError("Given object is not a module!")
        with self.mutex:
            self._processed_list.append(module)

    def is_processed_by(self, module):
        """Return True if the IU is processed by the given module.

        If the given object is a module that has not processed this IU or is not
        a module it returns False.

        Args:
            module (AbstractModule): The module to test whether or not it has
                processed the IU

        Returns:
            bool: Whether or not the module has processed the IU.
        """
        with self.mutex:
            return module in self._processed_list

    def __repr__(self):
        return "%s - (%s): %s" % (
            self.type(),
            self.creator.name(),
            str(self.payload)[0:10],
        )

    @staticmethod
    def type():
        """Return the type of the IU in a human-readable format.

        Returns:
            str: The type of the IU in a human-readable format.
        """
        raise NotImplementedError()


class AbstractModule:
    """An abstract module that is able to incrementally process data."""

    EVENT_PROCESS_IU = "process_iu"
    EVENT_SUBSCRIBE = "subscribe"
    EVENT_START = "start"
    EVENT_STOP = "stop"

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

    def get_init_arguments(self):
        """Returns the arguments of the init function to create the current
        instance of the Module.

        Returns:
            dict: A dictionary containing all the necessary arguments to create
            the current instance of the module.
        """
        d = {}
        valid_types = (int, float, bool, str, dict)  # Only serializable types.
        for k, v in self.__dict__.items():
            if isinstance(v, valid_types):
                d[k] = v
        return d

    def __init__(self, queue_class=IncrementalQueue, meta_data={}, **kwargs):
        """Initialize the module with a default IncrementalQueue.

        Args:
            queue_class (IncrementalQueue): A queue class that should be used
                instead of the standard queue class. If the given object does
                not inherit from IncrementalQueue, the standard IncrementalQueue
                is used.
            meta_data (dict): A dict with meta data about the module. This may
                be coordinates of the visualization of this module or other
                auxiliary information.
        """
        self._right_buffers = []
        self.is_running = False
        self._previous_iu = None
        self._left_buffers = []
        self.mutex = threading.Lock()
        self.events = {}

        self.meta_data = {}
        if meta_data:
            self.meta_data = meta_data

        self.queue_class = IncrementalQueue
        if issubclass(queue_class, IncrementalQueue):
            self.queue_class = queue_class

        self.iu_counter = 0

    def add_left_buffer(self, left_buffer):
        """Add a new left buffer for the module.

        This method stops the execution of the module pipeline if it is running.

        Args:
            left_buffer (IncrementalQueue): The left buffer to add to the
                module.
        """
        if not left_buffer or not isinstance(left_buffer, IncrementalQueue):
            return
        if self.is_running:
            self.stop()
        self._left_buffers.append(left_buffer)

    def remove_left_buffer(self, left_buffer):
        """Remove a left buffer from the module.

        This method stops the execution of the module pipeline if it is running.

        Args:
            left_buffer (IncrementalQueue): The left buffer to remove from the
                module.
        """
        if self.is_running:
            self.stop()
        self._left_buffers.remove(left_buffer)

    def left_buffers(self):
        """Returns the list of left buffers of the module.

        Returns:
            list: The left buffers of the module.
        """
        return list(self._left_buffers)

    def add_right_buffer(self, right_buffer):
        """Add a new right buffer for the module.

        This method stops the execution of the module pipeline if it is running.

        Args:
            right_buffer (IncrementalQueue): The right buffer to add to the
                module.
        """
        if not right_buffer or not isinstance(right_buffer, IncrementalQueue):
            return
        if self.is_running:
            self.stop()
        self._right_buffers.append(right_buffer)

    def remove_right_buffer(self, right_buffer):
        """Remove a right buffer from the module.

        This method stops the execution of the module pipeline if it is running.

        Args:
            right_buffer (IncrementalQueue): The right buffer to remove from the
                module.
        """
        if self.is_running:
            self.stop()
        self._right_buffers.remove(right_buffer)

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
            raise TypeError("IU is of type %s but should be IncrementalUnit" % type(iu))
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
            self.event_call(self.EVENT_SUBSCRIBE, {"module": module})
            q = self.queue_class(self, module)
            module.add_left_buffer(q)
        self._right_buffers.append(q)
        return q

    def remove_from_rb(self, module):
        """Removes the connection to a module from the right buffers.

        This method removes all queues between this module and the given module
        from the right buffer of this module and the left buffer of the given
        module.
        This method stops the execution of the module.

        Args:
            module: A module that is subscribed to this module
        """
        if self.is_running:
            self.stop()
        # We get a copy of the buffers because we are mutating it
        rbs = self.right_buffers()
        for buffer in rbs:
            if buffer.consumer == module:
                buffer.remove()

    def remove_from_lb(self, module):
        """Removes the connection to a module from the left buffers.

        This method removes all queues between this module and the given module
        from the left buffer of this module and the right buffer of the given
        module.
        This method stops the execution of the module.

        Args:
            module: A module that this module is subscribed to
        """
        if self.is_running:
            self.stop()
        # We get a copy of the buffers because we are mutating it
        lbs = self.left_buffers()
        for buffer in lbs:
            if buffer.producer == module:
                buffer.remove()

    def remove(self):
        """Removes all connections to all modules.

        This methods removes all queues from the left buffer and right buffer.
        The queues are also removed from the buffers of the connected modules.
        This method can be used to remove a module completely from a network.

        This method stops the execution of the module.
        """
        if self.is_running:
            self.stop()
        lbs = self.left_buffers()
        rbs = self.right_buffers()
        for buffer in lbs:
            buffer.remove()
        for buffer in rbs:
            buffer.remove()

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
        self.prepare_run()
        self.is_running = True
        while self.is_running:
            for buffer in self._left_buffers:
                with self.mutex:
                    try:
                        input_iu = buffer.get(timeout=QUEUE_TIMEOUT)
                    except queue.Empty:
                        input_iu = None
                    if input_iu:
                        if not self.is_valid_input_iu(input_iu):
                            raise TypeError(
                                "This module can't handle this " "type of IU"
                            )
                        self.event_call(self.EVENT_PROCESS_IU, {"iu": input_iu})
                        output_iu = self.process_iu(input_iu)
                        input_iu.set_processed(self)
                        if output_iu:
                            if self.output_iu() is not None or isinstance(
                                output_iu, self.output_iu()
                            ):
                                self.append(output_iu)
                            else:
                                raise TypeError(
                                    "This module should not produce"
                                    " IUs of this type."
                                )
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
            raise TypeError("IU is of type %s but should be IncrementalUnit" % type(iu))
        for valid_iu in self.input_ius():
            if isinstance(iu, valid_iu):
                return True
        return False

    def setup(self):
        """This method is called before the module is run. This method can be
        used to set up the pipeline needed for processing the IUs.

        However, after the setup method is called, the module may not
        immediately be run. For code that should be executed immediately before
        a module is run use the `prepare_run` method.
        """
        pass

    def prepare_run(self):
        """A method that is executed just before the module is being run.

        While this method may seem similar to `setup`, it is called immediately
        before the run routine. This method may be used in producing modules to
        initialize the generation of output IUs. Other than the `setup` method,
        this method makes sure that other modules in the network are also
        already setup.
        """
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
        for q in self.right_buffers():
            with q.mutex:
                q.queue.clear()
        t = threading.Thread(target=self._run)
        t.start()
        self.event_call(self.EVENT_START)

    def stop(self, clear_buffer=True):
        """Stops the execution of the processing pipeline of this module at the
        next possible point in time. This may be after the next incoming IU is
        processed."""
        self.is_running = False
        if clear_buffer:
            for buffer in self.right_buffers():
                while not buffer.empty():
                    buffer.get()
        self.event_call(self.EVENT_STOP)

    def create_iu(self, grounded_in=None):
        """Creates a new Incremental Unit that contains the information of the
        creator (the current module), the previous IU that was created in this
        module and the iu that it is based on.

        Do not discard (as in not using) any IU that was created by this method,
        because it will alreade have been introduced into the chain of IUs of
        this module!

        Args:
            grounded_in (IncrementalUnit): The incremental unit that the new
                unit is based on. May be None.

        Returns:
            IncrementalUnit: A new incremental unit with correct pointer to
            unit it is grounded in and to the previous IU that was generated by
            this module.
        """
        new_iu = self.output_iu()(
            creator=self,
            iuid=self.iu_counter,
            previous_iu=self._previous_iu,
            grounded_in=grounded_in,
        )
        self.iu_counter += 1
        self._previous_iu = new_iu
        return new_iu

    def latest_iu(self):
        """Provides reading access to the latest incremental unit that was
        produced by this module.

        Thus, the information received by this method might be out of date or
        completely wrong (in case where a not yet initialized IU is returned).
        The iu returned should not be modified in any way, because it could
        still be processed by a module.

        Return:
            (IncrementalUnit): The latest IU that was produced by the module.
        """
        return self._previous_iu

    def __repr__(self):
        return self.name()

    def event_subscribe(self, event_name, callback):
        """
        Subscribe a callback to an event with the given name. If tge event name
        is "*", then the callback will be called after every event.

        The callback function is given three arguments: the module that
        triggered the event (AbstractModule), the name of the event (str) and a
        dict (dict) that may contain data relevant to the event.

        Args:
            event_name (str): The name of the event to subscribe to
            callback (function): A function that is called once the event occurs
        """
        if not self.events.get(event_name):
            self.events[event_name] = []
        self.events[event_name].append(callback)

    def event_call(self, event_name, data={}):
        """
        Calls all callback functions that are subscribed to the given event
        name with some data attached to it. The data is optional but should stay
        consistent with each call of the same event.

        If * is passed as the event name, no callback function is called.

        Event name should be a unique identifier to the event. "*" is not
        allowed as an event name.

        Args:
            event_name (str): The name of the event (not "*")
            data (dict): Optionally some data that is relevant to the event.
        """
        if data is None:
            data = {}
        if event_name == "*":
            return
        if self.events.get(event_name):
            for callback in self.events[event_name]:
                threading.Thread(target=callback, args=(self, event_name, data)).start()
        if self.events.get("*"):
            for callback in self.events["*"]:
                threading.Thread(target=callback, args=(self, event_name, data)).start()


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
        return []

    @staticmethod
    def output_iu():
        raise NotImplementedError()

    def __init__(self, queue_class=IncrementalQueue, **kwargs):
        super().__init__(queue_class=IncrementalQueue, **kwargs)

    def _run(self):
        self.prepare_run()
        self.is_running = True
        while self.is_running:
            with self.mutex:
                output_iu = self.process_iu(None)
                if output_iu:
                    if self.output_iu() is not None and isinstance(
                        output_iu, self.output_iu()
                    ):
                        self.append(output_iu)
                    else:
                        raise TypeError(
                            "This module should not produce IUs of " "this type."
                        )
        self.shutdown()

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
        return None

    def subscribe(self, module, q=None):
        raise ValueError("Consuming Modules do not produce any output")

    def process_iu(self, input_iu):
        raise NotImplementedError()


class AbstractTriggerModule(AbstractProducingModule):
    """An abstract trigger module that produces IU once a trigger method is
    called. Unless the module is triggered no IUs are produced"""

    @staticmethod
    def name():
        raise NotImplementedError()

    @staticmethod
    def description():
        raise NotImplementedError()

    @staticmethod
    def input_ius():
        return []

    @staticmethod
    def output_iu():
        raise NotImplementedError()

    def __init__(self, queue_class=IncrementalQueue, **kwargs):
        super().__init__(queue_class=IncrementalQueue, **kwargs)

    def _run(self):
        self.prepare_run()
        self.is_running = True
        while self.is_running:
            with self.mutex:
                time.sleep(0.05)
        self.shutdown()

    def process_iu(self, input_iu):
        return None

    def trigger(self, data={}):
        """The trigger method that should produce an IU and append it to the
        right buffer

        Args:
            data (dict): A dictionary with data that can be used for the trigger
        """
        raise NotImplementedError()
