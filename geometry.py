import math

def rectangle_size(length = 0, width = 0):
    """Calculates the area of a detected rectangle object."""
    # area = length * width
    return length * width


def circle_size(radius = 0):
    """Calculates the area of a detected circular object."""
    # area = pi * r * r
    return math.pi * (radius ** 2)


def get_color_description(color_hex):
    """Simulates color detection based on a hex code."""
    # Represents solution plan to dictate what is seen
    colors = {'#FF0000': 'Red', '#00FF00': 'Green', '#0000FF': 'Blue'}
    return colors.get(color_hex, "Unknown Color")