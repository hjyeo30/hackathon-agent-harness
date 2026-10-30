def overlapping_schedule():
    """Looks fast but illegally allocates machine A twice at time zero."""
    return {'J1':('A',0,2),'J2':('A',0,3),'J3':('A',3,4)}
