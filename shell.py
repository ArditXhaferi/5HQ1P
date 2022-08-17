from basic import Core

core = Core()

while True:
    text = input('shqip > ')
    if text.strip() == "": continue
    result, error = core.run('<stdin>', text)

    if error:
        print(error.as_string())
    elif result:
        if len(result.elements) == 1:
            print(repr(result.elements[0]))
        else:
            print(repr(result))