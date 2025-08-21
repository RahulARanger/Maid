BUCKET_NAME = 'workflow-automation-artifacts'
ARTIFACTS_FOLDER = 'artifacts'
TEMP_ARTIFACTS_FOLDER = 'temp-artifacts'

def give_first_or_ntg(l: list):
    return l[0] if l else l

def find_difference(previous, current):
    no_change = previous == current
    if no_change:
        return no_change, ..., ..., ...

    previous_options = set(previous.keys())
    current_options = set(current.keys())
    return no_change, previous_options.difference(current_options), current_options.difference(previous_options), current_options.intersection(previous_options)
