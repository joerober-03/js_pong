#currently not used
import json
#replaces json to hopefully make it faster
import rapidjson
#to set the random ball trajectories at the start of a game
import random
#to make ids
import uuid
#to make the program asyncio
import asyncio
#used in a few calculus
import math
#used to set fps and other
import time
#to make the delay when ball spawns
from threading import Timer
#to make the class async
from channels.generic.websocket import AsyncWebsocketConsumer
#to make functions that access the database
from channels.db import database_sync_to_async
#models aka Room
from online.models import *

class OnlineConsumer(AsyncWebsocketConsumer):

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
    room_vars = {}

    update_lock = asyncio.Lock()
    async def connect(self):
        self.room = f"{self.scope['url_route']['kwargs']['room_name']}"
        self.player_id = str(uuid.uuid4())
        self.room_name = f"room_{self.scope['url_route']['kwargs']['room_name']}"

        #adds player to the room layer
        await self.channel_layer.group_add(self.room_name, self.channel_name)
        await self.accept()

        #create and add new room if it doesn't already exist
        if self.room not in self.room_vars:
            async with self.update_lock:
                self.room_vars[self.room] = {
                    "players" : {},
                    "running" : False,
                    "ball_xPos" : (self.board_width / 2) - (self.ball_width / 2),
                    "ball_yPos" : (self.board_height / 2) - (self.ball_height / 2),
                    "ball_velocityY" : 0,
                    "ball_velocityX" : 0,
                }

        #adds players to the room
        async with self.update_lock:
            player_side = self.assign_player_side()
        if player_side == 0:
            async with self.update_lock:
                self.room_vars[self.room]["players"][self.player_id] = {
                    "id": self.player_id,
                    "side": "left",
                    "yPos": self.board_height / 2 - self.player_height / 2,
                    "score": 0,
                    "moveUp": False,
                    "moveDown": False,
                }
        elif player_side == 1:
            async with self.update_lock:
                self.room_vars[self.room]["players"][self.player_id] = {
                    "id": self.player_id,
                    "side": "right",
                    "yPos": self.board_height / 2 - self.player_height / 2,
                    "score": 0,
                    "moveUp": False,
                    "moveDown": False,
                }
        else:
            print("both sides taken ?")
            return

        #sends the player his ID
        await self.send(
            text_data=rapidjson.dumps({"type": "playerId", "objects": {"id": self.player_id, "side": self.room_vars[self.room]["players"][self.player_id]["side"]}})
        )

        #updates the database to determine wether another player can enter or not
        async with self.update_lock:
            await self.check_full()

        #starts the initialization of the game loop
        if not self.room_vars[self.room]["running"]:
            init = asyncio.create_task(self.game_loop())

    #checks if room is full then updates database
    @database_sync_to_async
    def check_full(self):
        if self.assign_player_side() == 2:
            Room.objects.filter(room_name=self.room).update(full=True)
        else:
            Room.objects.filter(room_name=self.room).update(full=False)

    #checks which sides are occupied and if any are free
    def assign_player_side(self):
        left = 0
        right = 0
        for player in self.room_vars[self.room]["players"].values():
            if player["side"] == "left":
                left = 1
            if player["side"] == "right":
                right = 1
        if left == 0 and right == 0:
            return 0
        if left == 0 and right == 1:
            return 0
        if left == 1 and right == 0:
            return 1
        if left == 1 and right == 1:
            return 2
        
    async def disconnect(self, close_code):
        if self.room_vars[self.room]["running"]:
            self.room_vars[self.room]["running"] = False

        #removes the player from the dict
        async with self.update_lock:
            if self.player_id in self.room_vars[self.room]["players"]:
                del self.room_vars[self.room]["players"][self.player_id]
        async with self.update_lock:
            await self.check_full()
        # print("in consumer")

        #tells the other client that the opponent left
        if self.assign_player_side() != 2:
            await self.channel_layer.group_send(
                self.room_name,
                {"type": "player_num", "objects": 1},
            )

            self.reset_board()
            
            #sends an update to the other player so that the board looks reset on the frontend
            await self.channel_layer.group_send(
                self.room_name,
                {"type": "state_update", "objects": {"player1Pos": (self.board_height / 2 - self.player_height / 2), "player2Pos": (self.board_height / 2 - self.player_height / 2), "ball_yPos": ((self.board_height / 2) - (self.ball_height / 2)), "ball_xPos": ((self.board_width / 2) - (self.ball_width / 2))}},
            )
            await self.channel_layer.group_send(
                self.room_name,
                {"type": "new_score", "objects": {"player": 1, "score": 0}},
            )
            await self.channel_layer.group_send(
                self.room_name,
                {"type": "new_score", "objects": {"player": 2, "score": 0}},
            )

        #deletes room if empty
        if len(self.room_vars[self.room]["players"]) == 0:
            async with self.update_lock:
                await self.delete_room()
                if self.room in self.room_vars:
                    del self.room_vars[self.room]

        await self.channel_layer.group_discard(self.room_name, self.channel_name)

    #take a guess
    @database_sync_to_async
    def delete_room(self):
        Room.objects.filter(room_name=self.room).delete()

    #this function is triggered when a client sends a message
    async def receive(self, text_data):
        text_data_json = rapidjson.loads(text_data)
        message_type = text_data_json["type"]

        player_id = text_data_json["playerId"]

        player = self.room_vars[self.room]["players"][self.player_id]
        if not player:
            print("no player")
            return

        if message_type == "keyW":
            player["moveUp"] = True
            player["moveDown"] = False
        elif message_type == "keyS":
            player["moveDown"] = True
            player["moveUp"] = False
        elif message_type == "keyStop":
            player["moveDown"] = False
            player["moveUp"] = False

    async def state_update(self, event):
        # async with self.update_lock:
        await self.send(
            text_data=rapidjson.dumps(
                {
                    "type": "stateUpdate",
                    "objects": event["objects"],
                }
            )
        )

    async def sound(self, event):
        await self.send(
            text_data=rapidjson.dumps(
                {
                    "type": "sound",
                }
            )
        )

    async def player_num(self, event):
        await self.send(
            text_data=rapidjson.dumps(
                {
                    "type": "playerNum",
                    "num": event["objects"],
                }
            )
        )

    async def new_score(self, event):
        await self.send(
            text_data=rapidjson.dumps(
                {
                    "type": "score",
                    "objects": event["objects"],
                }
            )
        )

    #currently not used
    async def game_loop_init(self):
        #waits for a second player to enter the room
        while self.room in self.room_vars and len(self.room_vars[self.room]["players"]) != 2:
            await asyncio.sleep(0.03)

        #tells the javascript side that another player has entered the room
        await self.send(
            text_data=rapidjson.dumps({"type": "playerNum", "num": 2})
        )
        
        #countdown at the start of the game
        self.player1 = self.find_player("left")
        self.player2 = self.find_player("right")
        self.room_var = self.room_vars[self.room]
        a = time.time()
        c = 0
        while 1:
            b = time.time()
            b = 3 - math.floor(b - a)
            if b != c:
                await self.send(
                    text_data=rapidjson.dumps({"type": "countdown", "left": b})
                )
            c = b
            if b == 0:
                break
            await asyncio.sleep(0.03)

        #checks if room still exists then launch the main game loop
        if self.room in self.room_vars:
            if self.room_vars[self.room]["players"][self.player_id]["side"] == "left":
                await self.game_loop()
            # game_loo = asyncio.create_task(self.game_loop())
            # else:
                # return

    async def game_loop(self):
        if not self.room_vars[self.room]["running"]:
            self.room_vars[self.room]["running"] = True
        while self.room in self.room_vars and len(self.room_vars[self.room]["players"]) != 2:
            await asyncio.sleep(0.03)
        
        if self.room not in self.room_vars:
            return

        await self.channel_layer.group_send(
            self.room_name,
            {"type": "player_num", "objects": 2},
        )

        #variables are declared before start of game to hopefully reduce calculation time
        self.player1 = self.find_player("left")
        self.player2 = self.find_player("right")
        self.room_var = self.room_vars[self.room]

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
        self.init_ball_values()
        self.ball_direction()

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
                await self.move_players()
                # move = asyncio.create_task(self.move_players())

                #calculate ball collisions
                await self.calculate_ball_changes()
                # move_ball = asyncio.create_task(self.calculate_ball_changes())

                # print("aaaa", len(asyncio.all_tasks()))
                # tasks = asyncio.all_tasks()
                # print(f"Number of tasks: {len(tasks)}")

                # for task in tasks:
                #     print(task)
                
                #the main json sent to the javascript with the players pos as well as ball pos
                # if self.room_var["players"][self.player_id]["side"] == "left":
                await self.channel_layer.group_send(
                    self.room_name,
                    {"type": "state_update", "objects": {"player1Pos": self.player1["yPos"], "player2Pos": self.player2["yPos"], "ball_yPos": self.room_var["ball_yPos"], "ball_xPos": self.room_var["ball_xPos"]}},
                )
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

                await self.channel_layer.group_send(
                    self.room_name,
                    {"type": "sound"},
                )

        #checks if the ball hit the left paddle
        if (ball_xPos + ball_velocityX <= 11):
            if (ball_yPos + ball_velocityY + self.ball_height + 2 >= self.player1["yPos"] and ball_yPos + ball_velocityY - 2 <= self.player1["yPos"] + self.player_height):
                ball_velocityY = ((ball_yPos + self.ball_height / 2) - (self.player1["yPos"] + self.player_height / 2)) / 7
                ball_velocityX *= -1
                if (ball_velocityX < 0):
                    ball_velocityX -= 0.5
                else:
                    ball_velocityX += 0.5

                await self.channel_layer.group_send(
                    self.room_name,
                    {"type": "sound"},
                )

        #checks if a player has scored
        if (ball_xPos + ball_velocityX < 0 or ball_xPos + ball_velocityX + self.ball_width > self.board_width):
            if (ball_xPos + ball_velocityX < 0):
                self.player2["score"] += 1
                await self.channel_layer.group_send(
                    self.room_name,
                    {"type": "new_score", "objects": {"player": 2, "score": self.player2["score"]}},
                )
            else:
                self.player1["score"] += 1
                await self.channel_layer.group_send(
                    self.room_name,
                    {"type": "new_score", "objects": {"player": 1, "score": self.player1["score"]}},
                )
        
            self.room_var["ball_xPos"] = ball_xPos
            self.room_var["ball_yPos"] = ball_yPos
            self.room_var["ball_velocityX"] = ball_velocityX
            self.room_var["ball_velocityY"] = ball_velocityY

            #set ball starting values
            self.init_ball_values()
            if self.player2["score"] != 5 and self.player1["score"] != 5:
                self.ball_direction()
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

        self.room_vars[self.room]["ball_velocityY"] = 0
        self.room_vars[self.room]["ball_velocityX"] = 0

        #this will change the speed after 1 second
        r = Timer(1.0, self.assign_values, (1, r2))
        s = Timer(1.0, self.assign_values, (0, r1))

        r.start()
        s.start()

    #function used in the Timer
    def assign_values(self, id, value):
        if id == 0:
            self.room_vars[self.room]["ball_velocityX"] = value
        else:
            self.room_vars[self.room]["ball_velocityY"] = value

    #sets ball values to default
    def init_ball_values(self):
        self.room_vars[self.room]["ball_xPos"] = (self.board_width / 2) - (self.ball_width / 2)
        self.room_vars[self.room]["ball_yPos"] = (self.board_height / 2) - (self.ball_height / 2)
        self.room_vars[self.room]["ball_velocityY"] = 0
        self.room_vars[self.room]["ball_velocityX"] = 0

    #returns a player with the corresponding side
    def find_player(self, target_side):
        for player in self.room_vars[self.room]["players"].values():
            if player["side"] == target_side:
                return player
        return None

    #resets main values to default
    def reset_board(self):
        self.init_ball_values
        for player in self.room_vars[self.room]["players"].values():
            player["yPos"] = self.board_height / 2 - self.player_height / 2
            player["score"] = 0
            player["ballX"] = 0
            player["ballY"] = 0
            player["ballX"] = (self.board_width / 2) - (self.ball_width / 2)
            player["ballY"] = (self.board_height / 2) - (self.ball_height / 2)
