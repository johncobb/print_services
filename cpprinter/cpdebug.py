from decorator import decorator

@decorator
def debug_func(function, *args):
    print ('%s was called.' % function.func_name)
    return function(*args)
