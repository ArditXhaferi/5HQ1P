from basic import Core
import os.path

core = Core()

while True:
    index = os.path.abspath(__file__)
    parent = os.path.abspath(os.path.join(os.path.join(index, os.pardir), os.pardir))
    if os.path.exists(parent + "/index.sq"):
        result, error = core.run('<index.sq>', 'zbato("index.sq")')

        if error:
            print(error.as_string())
        break
    else:
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