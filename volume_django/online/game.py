#to set the random ball trajectories at the start of a game
import random
#to make the program asyncio
import asyncio
#used in a few calculus
import math
#used to set fps and other
import time
#to make the delay when ball spawns
from threading import Timer
#models aka Room
from online.models import *
from channels.generic.websocket import AsyncWebsocketConsumer
#other vars
# import game_struct
from .game_struct import room_vars, state_update

# #currently not used
#     async def game_loop_init(self):
#         #waits for a second player to enter the room
#         while self.room in room_vars and len(room_vars[self.room]["players"]) != 2:
#             await asyncio.sleep(0.03)

#         #tells the javascript side that another player has entered the room
#         await self.send_json({"type": "playerNum", "num": 2})
        
#         #countdown at the start of the game
#         self.player1 = self.find_player("left")
#         self.player2 = self.find_player("right")
#         self.room_var = room_vars[self.room]
#         a = time.time()
#         c = 0
#         while 1:
#             b = time.time()
#             b = 3 - math.floor(b - a)
#             if b != c:
#                 await self.send(
#                     text_data=rapidjson.dumps({"type": "countdown", "left": b})
#                 )
#             c = b
#             if b == 0:
#                 break
#             await asyncio.sleep(0.03)

#         #checks if room still exists then launch the main game loop
#         if self.room in room_vars:
#             if room_vars[self.room]["players"][self.player_id]["side"] == "left":
#                 await self.game_loop()
#             # game_loo = asyncio.create_task(self.game_loop())
#             # else:
#                 # return
class GameLoop(AsyncWebsocketConsumer):
    room = ""

    #board
    board_height = 800
    board_width = 1200

    #player
    player_height = 100
    playerVelocity = 15

    #balling
    ball_width = 15
    ball_height = 15
    ball_velocity = 10

    #where all the rooms are stored

    update_lock = asyncio.Lock()

    async def game_loop(self, game_room):
        self.room = game_room
        if not room_vars[self.room]["running"]:
            room_vars[self.room]["running"] = True
        while self.room in room_vars and len(room_vars[self.room]["players"]) != 2:
            await asyncio.sleep(0.03)
        
        if self.room not in room_vars:
            return

        #variables are declared before start of game to hopefully reduce calculation time
        self.player1 = self.find_player(self, "left")
        self.player2 = self.find_player(self, "right")
        self.room_var = room_vars[self.room]

        ##timer which seems to slow down the start of the game
        # a = time.time()
        # c = 0
        # while 1:
        #     b = time.time()
        #     b = 3 - math.floor(b - a)
        #     if b != c:
        #         await self.send(
        #             text_data=rapidjson.dumps({"type": "countdown", "left": b})
        #         )
        #     c = b
        #     if b == 0:
        #         break
        #     await asyncio.sleep(0.03)

        #initializes ball direction/position
        self.init_ball_values(self)
        self.ball_direction(self)

        #initialize fps restriction
        fpsInterval = 1.0 / 60.0
        then = asyncio.get_event_loop().time()

        #the main loop
        while len(self.room_var["players"]) == 2:

            #the 60 fps rule
            now = asyncio.get_event_loop().time()
            elapsed = now - then
            if (elapsed > fpsInterval):
                then = now - (elapsed % fpsInterval)

                #player movement
                await self.move_players(self)
                # move = asyncio.create_task(self.move_players())

                #calculate ball collisions
                await self.calculate_ball_changes(self)
                # move_ball = asyncio.create_task(self.calculate_ball_changes())

                # print("aaaa", len(asyncio.all_tasks()))
                # tasks = asyncio.all_tasks()
                # print(f"Number of tasks: {len(tasks)}")

                # for task in tasks:
                #     print(task)
                
                state_update["player1Pos"] = self.player1["yPos"]
                state_update["player2Pos"] = self.player2["yPos"]
                state_update["ball_yPos"] = self.room_var["ball_yPos"]
                state_update["ball_xPos"] = self.room_var["ball_xPos"]
                state_update["player1Score"] = self.player1["score"]
                state_update["player2Score"] = self.player2["score"]
                #the main json sent to the javascript with the players pos as well as ball pos
                # if self.room_var["players"][self.player_id]["side"] == "left":
                # await self.channel_layer.group_send(
                #     self.room_name,
                #     {"type": "state_update", "objects": {"player1Pos": self.player1["yPos"], "player2Pos": self.player2["yPos"], "ball_yPos": self.room_var["ball_yPos"], "ball_xPos": self.room_var["ball_xPos"]}},
                # )
                # test = asyncio.create_task(self.aw_hell_nah_that_shit_aint_gonna_work_bruh())

                #gives time to the rest of the processes to operate
                await asyncio.sleep(fpsInterval)

    # async def aw_hell_nah_that_shit_aint_gonna_work_bruh(self):
    #     await self.channel_layer.group_send(
    #         self.room_name,
    #         {"type": "state_update", "objects": {"player1Pos": self.player1["yPos"], "player2Pos": self.player2["yPos"], "ball_yPos": self.room_var["ball_yPos"], "ball_xPos": self.room_var["ball_xPos"]}},
    #     )

    #calculate player movement
    async def move_players(self):
        for player in self.room_var["players"].values():
            if player["moveUp"]:
                if player["yPos"] - self.playerVelocity > 0:
                    player["yPos"] -= self.playerVelocity
                else:
                    player["yPos"] = 0
            elif player["moveDown"]:
                if player["yPos"] + self.playerVelocity + self.player_height < self.board_height:
                    player["yPos"] += self.playerVelocity
                else:
                    player["yPos"] = self.board_height - self.player_height

    #most of the game logic/calculations are here
    async def calculate_ball_changes(self):

        #some variables are set to hopefully reduce calculation time
        ball_yPos = self.room_var["ball_yPos"]
        ball_xPos = self.room_var["ball_xPos"]
        ball_velocityY = self.room_var["ball_velocityY"]
        ball_velocityX = self.room_var["ball_velocityX"]

        if (not self.player1 or not self.player2 or not self.room_var):
            return

        #checks if ball hit the top or bottom
        if (ball_yPos + ball_velocityY < 0 or ball_yPos + ball_velocityY + self.ball_height > self.board_height):
            ball_velocityY *= -1

        #checks if the ball hit the right paddle
        if (ball_xPos + ball_velocityX + self.ball_width >= self.board_width - 11):
            if (ball_yPos + ball_velocityY + self.ball_height + 2 >= self.player2["yPos"] and ball_yPos + ball_velocityY - 2 <= self.player2["yPos"] + self.player_height):
                ball_velocityY = ((ball_yPos + self.ball_height / 2) - (self.player2["yPos"] + self.player_height / 2)) / 7
                ball_velocityX *= -1
                if ball_velocityX < 0:
                    ball_velocityX -= 0.5
                else:
                    ball_velocityX += 0.5
                
                state_update["sound"] = True

                

        #checks if the ball hit the left paddle
        if (ball_xPos + ball_velocityX <= 11):
            if (ball_yPos + ball_velocityY + self.ball_height + 2 >= self.player1["yPos"] and ball_yPos + ball_velocityY - 2 <= self.player1["yPos"] + self.player_height):
                ball_velocityY = ((ball_yPos + self.ball_height / 2) - (self.player1["yPos"] + self.player_height / 2)) / 7
                ball_velocityX *= -1
                if (ball_velocityX < 0):
                    ball_velocityX -= 0.5
                else:
                    ball_velocityX += 0.5

                state_update["sound"] = True

        #checks if a player has scored
        if (ball_xPos + ball_velocityX < 0 or ball_xPos + ball_velocityX + self.ball_width > self.board_width):
            if (ball_xPos + ball_velocityX < 0):
                self.player2["score"] += 1
            else:
                self.player1["score"] += 1
        
            self.room_var["ball_xPos"] = ball_xPos
            self.room_var["ball_yPos"] = ball_yPos
            self.room_var["ball_velocityX"] = ball_velocityX
            self.room_var["ball_velocityY"] = ball_velocityY

            #set ball starting values
            self.init_ball_values(self)
            if self.player2["score"] != 5 and self.player1["score"] != 5:
                self.ball_direction(self)
        else:
            self.room_var["ball_xPos"] = ball_xPos
            self.room_var["ball_yPos"] = ball_yPos
            self.room_var["ball_velocityX"] = ball_velocityX
            self.room_var["ball_velocityY"] = ball_velocityY

        self.room_var["ball_xPos"] += self.room_var["ball_velocityX"]
        self.room_var["ball_yPos"] += self.room_var["ball_velocityY"]

    #chooses a random direction for the ball to start
    def ball_direction(self):
        r1 = random.randint(0, 1)
        if r1 == 0:
            r1 = self.ball_velocity
        else:
            r1 = self.ball_velocity * -1
        
        r2 = 0
        while r2 == 0:
            r2 = random.randint(-5, 5)

        room_vars[self.room]["ball_velocityY"] = 0
        room_vars[self.room]["ball_velocityX"] = 0

        #this will change the speed after 1 second
        r = Timer(1.0, self.assign_values, (self, 1, r2))
        s = Timer(1.0, self.assign_values, (self, 0, r1))

        r.start()
        s.start()

    #function used in the Timer
    def assign_values(self, id, value):
        if id == 0:
            room_vars[self.room]["ball_velocityX"] = value
        else:
            room_vars[self.room]["ball_velocityY"] = value

    #sets ball values to default
    def init_ball_values(self):
        room_vars[self.room]["ball_xPos"] = (self.board_width / 2) - (self.ball_width / 2)
        room_vars[self.room]["ball_yPos"] = (self.board_height / 2) - (self.ball_height / 2)
        room_vars[self.room]["ball_velocityY"] = 0
        room_vars[self.room]["ball_velocityX"] = 0

    #returns a player with the corresponding side
    def find_player(self, target_side):
        for player in room_vars[self.room]["players"].values():
            if player["side"] == target_side:
                return player
        return None

    #resets main values to default
    def reset_board(self):
        self.init_ball_values(self)
        for player in room_vars[self.room]["players"].values():
            player["yPos"] = self.board_height / 2 - self.player_height / 2
            player["score"] = 0
