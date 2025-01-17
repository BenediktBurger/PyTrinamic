"""
Move a motor back and forth using velocity and position mode of the TMC2240
"""
import time
import pytrinamic
from pytrinamic.connections import ConnectionManager
from pytrinamic.evalboards import TMC2240_eval

pytrinamic.show_info()

with ConnectionManager().connect() as my_interface:
    print(my_interface)

    # Create TMC2240-EVAL class which communicates over the Landungsbrücke via TMCL
    eval_board = TMC2240_eval(my_interface)
    mc = eval_board.ics[0]
    motor = eval_board.motors[0]

    print("Preparing parameter...")
    motor.set_axis_parameter(motor.AP.MaxAcceleration, 20000)
    motor.set_axis_parameter(motor.AP.MaxVelocity, 100000)
    motor.set_axis_parameter(motor.AP.MaxCurrent, 30)

    # Clear actual positions
    motor.actual_position = 0

    print("Rotating...")
    motor.rotate(7*25600)
    time.sleep(5)

    print("Stopping...")
    motor.stop()
    time.sleep(1)

    print("Moving back to 0...")
    motor.move_to(0, 100000)

    # Wait until position 0 is reached
    while motor.actual_position != 0:
        print("Actual position: " + str(motor.actual_position))
        time.sleep(0.2)

    print("Reached position 0")

print("\nReady.")
