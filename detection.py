class DetectedObject:
    """Base class for any object found in the camera's field of view."""

    def __init__(self, color = "Unknown"):
        self.color = color
    

class DetectedRectangle(DetectedObject):
    """Derived class for rectangular objects inheriting from DetectedObject."""

    def __init__(self, length, width, color):
        super().__init__(color)
        self.length = length
        self.width = width
    

    def get_narrative(self):
        """Generates the string to be dictated to the user."""
        area = self.length * self.width
        # Uses formatted string literals for clear output
        return f"A {self.color} rectangle with a size of {area} square units."