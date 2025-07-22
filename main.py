import pseudo

while True: 
    text = input('>>>')
    result, error = pseudo.run('<stdn>',text)

    if error: 
        print(error.as_string())
    elif result: 
        print(repr(result))