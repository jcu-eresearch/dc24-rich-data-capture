from abc import abstractmethod

__author__ = 'Casey Bajema'

class _ProcessingScript():
    """
    Abstract processing script that should be sub-classed to provide datasets with custom processing.
    """
    @abstractmethod
    def process_it(self, data_entry):
        """
        Process the data_entry in some way and return the result(s)

        :param data_entry: The received data_entry object
        :return: None, a data_entry object or an array of data_entry objects that are ready to re-ingest or store.
        """
        pass

class _SamplingScript():
    """
    Abstract sampling script that should be sub-classed to provide custom data sampling times.
    """
    def is_sample(self, datetime):
        """
        Test if the ingester should use the data at the given time

        :param datetime: Datetime representing the date and time to the millisecond.
        :return: True or False if the ingester should sample at the time given.
        """
        pass
