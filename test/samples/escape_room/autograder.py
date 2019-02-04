from grading_escape_room import EscapeRoom
import unittest, re, itertools

def iterCodes(digits):
    # if there are four "smudge" digits, all possible codes are just permutations
    if len(digits) == 4:
        return itertools.permutations(digits)
    else:
        # otherwise, we need to do a product of all the digits to get repeats
        # but this give us too many. So exclude ones that don't include all digits
        return (p for p in itertools.product(digits, repeat=4) if set(p) == set(digits))

class ExpectedOutput:
    def __init__(self):
        self.time = 0
        self.player_inventory = []
        self.glasses = False
        self.look_mirror = False
        self.chest_locked = False
        self.chest_open = False
        self.look_floor = False
        self.board_open = False
        self.door_locked = False
        self.digits = ""
        self.escape_code = None
        self.door_open = False
        
    def expected_look(self, object=None):
        if object == None or object == "":
            return """You are in a locked room. There is only one door
and it has a numeric keypad. Above the door is a clock that reads {}.
Across from the door is a large mirror. Below the mirror is an old chest.

The room is old and musty and the floor is creaky and warped.""".format(self.time)
        elif object == "door":
            if self.glasses == False:
                return "The door is strong and highly secured. The door is locked and requires a 4-digit code to open."
            else:
                return "The door is strong and highly secured. The door is locked and requires a 4-digit code to open. But now you're wearing these glasses you notice something! There are smudges on the digits {}.".format(self.digits)
        elif object == "mirror":
            if "hairpin" not in self.player_inventory:
                return "You look in the mirror and see yourself... wait, there's a hairpin in your hair. Where did that come from?"
            else:
                return "You look in the mirror and see yourself."
                
        elif object == "floor":
            return "The floor makes you nervous. It feels like it could fall in. One of the boards is loose."
            
        elif object == "board":
            if not self.look_floor:
                return ""
            elif not self.board_open:
                return "The board is loose, but won't come up when you pull on it. Maybe if you pried it open with something."
            else:
                return "The board has been pulled open. You can look inside."
        return template
        
    def expected_get(self, object, container=None):
        if object == None or object == "":
            return ""
        elif object in self.player_inventory:
            return "You already have"
        elif container != None:
            if container == "chest":
                if not self.chest_open:
                    return ""
                elif object in ["hammer"]:
                    return "You got it."
                else:
                    return "You don't see that."
            elif container == "board":
                if not self.board_open:
                    return ""
                elif object in ["glasses"]:
                    return "You got it."
                else:
                    return "You don't see that."
            else:
                return ""
        elif object == "hairpin":
            if self.look_mirror:
                return "You got it."
            else:
                return "You don't see that."
        else:
            return "You don't see that."
            
    def expected_unlock(self, object, unlock_with):
        if object == None or object == "":
            return ""
        elif unlock_with == None or unlock_with == "":
            return ""
        elif object == "chest":
            if unlock_with not in self.player_inventory:
                return ""
            elif unlock_with == "hairpin":
                return "You hear a click! It worked!"
            else:
                return ""
        elif object == "door":
            if len(unlock_with) != 4 or not unlock_with.isnumeric():
                return ""
            elif unlock_with == self.escape_code:
                return "You hear a click! It worked!"
            else:
                return "That's not the right code!"
        else:
            return "You don't see that here."
            
    def expected_open(self, object):
        if object == None or object == "":
            return ""
        elif object == "chest":
            if self.chest_locked:
                return ""
            elif self.chest_open:
                return ""
            else:
                return "You open the chest."
        elif object == "door":
            if self.door_locked:
                return ""
            elif self.door_open:
                return ""
            else:   
                return "You open the door."
        else:
            return "You don't see that."
            
    def expected_pry(self, object, tool):
        if object in [None, ""]:
            return ""
        elif tool in [None, ""]:
            return ""
        elif object == "board":
            if not self.look_floor:
                return ""
            if tool == "hammer":
                if "hammer" not in self.player_inventory:
                    return ""
                elif self.board_open:
                    return ""
                else:
                    return "You use the hammer to pry open the board. It takes some work, but with some blood and sweat, you manage to get it open."
        else:
            return ""
            
    def expected_wear(self, object):
        if object in [None, ""]:
            return ""
        elif object == "glasses":
            if "glasses" not in self.player_inventory:
                return ""
            elif self.glasses:
                return ""
            else:
                return "You are now wearing the glasses."
        else:
            return ""
                

class TestLegalCommands(unittest.TestCase):
    """
    This only tests commands that should work, not commands that
    should fail.
    """
    def setUp(self):
        self.room = EscapeRoom()
        self.room.start()
        self.expected_output = ExpectedOutput()
        self.game_time = 100
        
        # initial game state
        self.expected_output.chest_locked = True
        self.expected_output.door_locked = True
        
    def execute_game_command(self, command):
        output = self.room.command(command)
        self.game_time -= 1
        return output
        
    def test_standard_walkthrough(self):
        # check initial status is locked
        self.assertEqual(self.room.status(), "locked")
        
        # check look mirror
        self.expected_output.time = self.game_time
        expected_output = self.expected_output.expected_look("mirror")
        game_output = self.execute_game_command("look mirror")
        self.assertEqual(game_output, expected_output)
        
        # check get hairpin
        # We have looked in the mirror. Set the state
        self.expected_output.look_mirror = True
        self.expected_output.time = self.game_time
        expected_output = self.expected_output.expected_get("hairpin")
        game_output = self.execute_game_command("get hairpin")
        self.assertEqual(game_output, expected_output)
        
        # unlock chest
        # we have the hairpin, so add it to inventory
        self.expected_output.player_inventory.append("hairpin")
        self.expected_output.time = self.game_time
        expected_output = self.expected_output.expected_unlock("chest", "hairpin")
        game_output = self.execute_game_command("unlock chest with hairpin")
        self.assertEqual(game_output, expected_output)
        
        # open chest
        # we have unlocked the chest, so set that
        self.expected_output.chest_locked = False
        self.expected_output.time = self.game_time
        expected_output = self.expected_output.expected_open("chest")
        game_output = self.execute_game_command("open chest")
        self.assertEqual(game_output, expected_output)
        
        # get hammer from chest
        # set the chest open
        self.expected_output.chest_open = True
        self.expected_output.time = self.game_time
        expected_output = self.expected_output.expected_get("hammer", "chest")
        game_output = self.execute_game_command("get hammer from chest")
        self.assertEqual(game_output, expected_output)
        
        # look floor
        self.expected_output.time = self.game_time
        expected_output = self.expected_output.expected_look("floor")
        game_output = self.execute_game_command("look floor")
        self.assertEqual(game_output, expected_output)
        
        # look board
        # We've looked at the floor.
        self.expected_output.look_floor = True
        expected_output = self.expected_output.expected_look("board")
        game_output = self.execute_game_command("look board")
        self.assertEqual(game_output, expected_output)
        
        # pry board with hammer
        # We have the hammer
        self.expected_output.player_inventory.append("hammer")
        self.expected_output.time = self.game_time
        expected_output = self.expected_output.expected_pry("board", "hammer")
        game_output = self.execute_game_command("pry board with hammer")
        self.assertEqual(game_output, expected_output)
        
        # get glasses from board
        # we have the board open
        self.expected_output.board_open = True
        self.expected_output.time = self.game_time
        expected_output = self.expected_output.expected_get("glasses", "board")
        game_output = self.execute_game_command("get glasses from board")
        self.assertEqual(game_output, expected_output)
        
        # wear glasses
        # we have the glasses
        self.expected_output.player_inventory.append("glasses")
        self.expected_output.time = self.game_time
        expected_output = self.expected_output.expected_wear("glasses")
        game_output = self.execute_game_command("wear glasses")
        self.assertEqual(game_output, expected_output)
        
        # look door
        # we have the glasses on
        self.expected_output.glasses = True
        self.expected_output.time = self.game_time
        
        # run the game command. We have to do it first to get the digits
        # note, we got the game time first.
        game_output = self.execute_game_command("look door")
        
        # the game_output should have the digits. We can't
        # do a straight comparison. The digits will be everything
        # from the word "digits" to the period
        self.assertTrue("digits " in game_output)
        self.assertTrue(game_output[-1] == ".")
        digitsStart = game_output.index("digits ") + len("digits ")
        digitsEnd = -1
        digits = game_output[digitsStart : digitsEnd]
        
        # verify the digits. There should be no more than 4, and
        # in sorted order. Must either be separated by a comma
        # or a comma and a space
        if ", " in digits:
            digitsSplit = digits.split(", ")
        else:
            digitsSplit = digits.split(",")
        
        digitInts = [int(d) for d in digitsSplit]
        for i in range(len(digitInts)-1):
            self.assertTrue(digitInts[i] < digitInts[i+1], "{} not correct format.".format(digits))
        
        # now we have the digits, we can get the output
        self.expected_output.digits = digits
        expected_output = self.expected_output.expected_look("door")
        
        self.assertEqual(game_output, expected_output)
        
        # Try codes until we escape
        for code in iterCodes(digitInts):
            codeString = "".join([str(digit) for digit in code])
            
            # get the time first
            self.expected_output.time = self.game_time
            
            # now execute the command to see if we succeeded
            game_output = self.execute_game_command("unlock door with {}".format(codeString))
            
            # the game will have one of two outputs. We don't know which one.
            # try both
            
            # this will give us the error output, because escape code doesn't match
            expected_locked_output = self.expected_output.expected_unlock("door",codeString)
            
            # this will give us the successoutput because escape code matches
            self.expected_output.escape_code = codeString
            expected_unlocked_output = self.expected_output.expected_unlock("door", codeString)
            
            self.assertTrue(game_output in [expected_locked_output, expected_unlocked_output],
            "Unlock output not either expected version.\nActual: {}\nExpected Locked: {}\nExpected Unlocked:{}".format(game_output, expected_locked_output, expected_unlocked_output))
            
            # if code matched, break the loop
            if game_output == expected_unlocked_output:
                break

        # now we've unlocked, open the door
        self.expected_output.time = self.game_time
        self.expected_output.door_locked = False
        game_output = self.execute_game_command("open door")
        expected_output = self.expected_output.expected_open("door")
        self.assertEqual(game_output, expected_output)
        
        # we should be done. Check status
        self.assertEqual(self.room.status(), "escaped")

if __name__ == '__main__':
    unittest.main()