def zero_fill_spikes(readings,baseline=10,delta=3):
    """Wrong: missing measurements become fabricated zero-temperature spikes."""
    return [t for t,v in readings if abs((0 if v is None else v)-baseline)>delta]
