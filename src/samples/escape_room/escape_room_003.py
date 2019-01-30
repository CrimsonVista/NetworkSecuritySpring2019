
door = "closed"
locked = True
code = 1234
while door == "closed":
    command = input(">> ")
    commandParts = command.split(" ")
    command = commandParts[0]
    if command == "open":
        if len(commandParts) == 1:
            print("Open what?")
            continue
        object = commandParts[1]
        if object == "door":
            if locked:
                print("you can't open the door! It's locked")
            else:
                print("you open the door")
                door = "open"
        else:
            print("You don't know how to open that.")
    elif command == "unlock":
        if len(commandParts) <3:
            print("Unlock what with what?")
            continue
        object = commandParts[1]
        code = commandParts[-1]
        if object == "door":
            if code == str(code):
                print("That's the correct code! The door unlocks!")
                locked = False
            else:
                print("That's the wrong code!")
        else:
            print("You don't know how to unlock that.")
    else:
        print("you don't know how to do that.")
print("congrautlations! You escaped")