from abc import abstractmethod

__author__ = 'Casey Bajema'

"""
    Base sampling object that defines the type.

    The intended usage is for the ingester platform to poll sample_now at regular intervals and run the
    ingester when it returns True.
"""
class _Sampling(dict):
    """
        Test if the ingester should run at the given point in time specified by datetime.

        @datetime - Should the ingester be run at the given time
        @poll_rate - Time in milliseconds between calls to sample_now
        @return True/False
    """
    @abstractmethod
    def sample_now(self, datetime, poll_rate=1):
        pass


"""
    Use a custom python script to provide sampling times

    The maximum size of the script is defined by MAX_SCRIPT_SIZE
"""
class CustomSampling(_Sampling):
    MAX_SCRIPT_SIZE = 1000000

    def __init__(self, script_handle):
        self.script = script_handle

    def sample_now(self, datetime):
        self.datetime = datetime

        file = open(script, 'r')

        eval(file.read(self.MAX_SCRIPT_SIZE), poll_rate=1)

        return self.result

"""
    Sample based on a map of datetime/repeat rate pairs allowing the user to set an unlimited number of
    repeating times to sample on.
"""
class RepeatSampling(_Sampling):
    # Repeat rates
    microsecond, millisecond, second, minute, hour, day, week, month, year = range(9)

    """
        @sample_times - map of datetime/repeat rate pairs.
    """
    def __init__(self, sample_times):
        # TODO: Validate the sample_times
        self.sample_times = sample_times

    def sample_now(self, datetime):
        # TODO: Implement the sampling times.
        pass

