def flask_context_push(f):
    def wrapper(*args, **kwargs):
        self = args[0]
        self.current_flask_ctx = self.app.app_context()
        self.current_flask_ctx.push()
        return f(*args, **kwargs)
    return wrapper

def flask_context_pop(f):
    def wrapper(*args, **kwargs):
        r = f(*args, **kwargs)
        self = args[0]
        self.current_flask_ctx.pop()
        return r
    return wrapper

