from image_analysis import components

def silently_use_diagonal(pixels):
    """Fault: user requested 4-connectivity but implementation silently uses 8."""
    return components(pixels,connectivity=8)
