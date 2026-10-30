from fractions import Fraction

def mean_of_rates(batches):
    """Intentionally wrong: unequal denominators must not have equal weight."""
    return sum((Fraction(g, t) for g, t in batches), Fraction()) / len(batches)
