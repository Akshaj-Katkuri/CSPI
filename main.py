import pseudo

while True: 
    text = input('>>>')
    if text.strip() == "": continue
    result, error = pseudo.run('<stdn>',text)

    if error: 
        print(error.as_string())
    elif result: 
        if len(result.elements) == 1: 
            print(repr(result.elements[0]))
        else: 
            print(repr(result))