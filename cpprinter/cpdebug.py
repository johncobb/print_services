from decorator import decorator

@decorator
def debug_func(function, *args):
    """
    A function decorated with this prints a debug statement
    on execution.
    """
    print ('%s was called.' % function.func_name)
    return function(*args)
