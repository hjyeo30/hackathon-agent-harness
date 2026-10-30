from model import Model

def fit_with_test_imputation(train, test):
    """Wrong: test features influence training preprocessing."""
    observed=[x for x,_ in train+test if x is not None]
    fill=sum(observed)/len(observed)
    groups={label:[fill if x is None else x for x,y in train if y==label] for label in (0,1)}
    return Model(fill,sum(groups[0])/len(groups[0]),sum(groups[1])/len(groups[1]))
