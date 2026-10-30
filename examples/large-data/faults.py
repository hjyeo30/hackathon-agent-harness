def mean_of_chunk_means(values,chunk_size):
    """Wrong when the final chunk has fewer rows."""
    means=[sum(values[i:i+chunk_size])/len(values[i:i+chunk_size]) for i in range(0,len(values),chunk_size)]
    return sum(means)/len(means)
