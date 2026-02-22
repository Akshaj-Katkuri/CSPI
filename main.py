from interpreter import run

while True:
    text = input(">>>")
    if text.strip() == "":
        continue
    result, error = run("<stdn>", text)

    if error:
        print(error.as_string())
