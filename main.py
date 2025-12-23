from interpreter import run
from robot.robot import Robot

robot = Robot()

while True: 
    text = input('>>>')
    if text.strip() == "": continue
    # Pass the Robot instance into the interpreter so built-ins can use it
    result, error = run('<stdn>', text, robot=robot)

    if error: 
        print(error.as_string())
