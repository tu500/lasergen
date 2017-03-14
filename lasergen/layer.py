class Layer():
    """
    Stores layer information including main layer, warning level and warning
    data.
    """

    def __init__(self, name, warn_level=None, warnings=None):

        if warnings is None:
            warnings = []

        self.name = name
        self.warn_level = warn_level
        self.warnings = warnings

    @staticmethod
    def warn(warning):
        """
        Create empty warn layer object.
        """

        return Layer(None, 'warn', [warning])

    @staticmethod
    def error(warning):
        """
        Create empty error layer object.
        """

        return Layer(None, 'error', [warning])

    def combine(self, other):
        """
        Combine data with the given layer's, merging warning level information.

        Raises an exception if the main layer does not match.
        """

        name = self.name
        warnings = self.warnings + other.warnings
        warn_level = self.warn_level

        if other.name is not None:
            assert(self.name is None or self.name == other.name)
            name = other.name

        if self.warn_level is None or (self.warn_level == 'warn' and other.warn_level == 'error'):
            warn_level = other.warn_level

        return Layer(name, warn_level, warnings)

    def compatible(self, other):
        """
        Check whether main layer data matches the given layer's.
        """

        return self.name == other.name

    def __eq__(self, other):
        """
        Check whether main layer data and warning level matches the given layer's.
        """

        return self.name == other.name and self.warn_level == other.warn_level
