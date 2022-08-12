from basic import Core

core = Core()

while True:
    text = input('shqip > ')
    result, error = core.run('<stdin>', text)

    if error: print(error.as_string())
    elif result: print(repr(result))