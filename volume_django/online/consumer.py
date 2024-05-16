import json
import random
import uuid
import asyncio
import math
import time
from threading import Timer
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from online.models import *

class OnlineConsumer(AsyncWebsocketConsumer):

    #board
    board_height = 800
    board_width = 1200

    #player
    player_width = 15
    player_height = 100
    playerVelocity = 15

    #balling
    ball_width = 15
    ball_height = 15
    ball_velocity = 10

    #these variables are changed to decide wether to send certain jsons or not
    bounce = False
    score = 0

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

        #sends the player his ID
        await self.send(
            text_data=json.dumps({"type": "playerId", "playerId": self.player_id})
        )

        #add new room if it doesn't already exist
        if self.room not in self.room_vars:
            async with self.update_lock:
                self.room_vars[self.room] = {
                    "players" : {},
                    "player_num" : 0,
                    "stop" : False,
                    "ball_xPos" : (self.board_width / 2) - (self.ball_width / 2),
                    "ball_yPos" : (self.board_height / 2) - (self.ball_height / 2),
                    "ball_velocityY" : 0,
                    "ball_velocityX" : 0,
                }

        #adds players to the room
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

        #updates the database to determine wether another player can enter or not
        await self.check_full()

        #starts the initialization of the game loop
        # await self.game_loop_init()
        # if len(self.room_vars[self.room]["players"]) == 1:
        init = asyncio.create_task(self.game_loop_init())

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
        #removes the player from the dict
        async with self.update_lock:
            if self.player_id in self.room_vars[self.room]["players"]:
                del self.room_vars[self.room]["players"][self.player_id]

        #tells the other client that the opponent left
        if self.assign_player_side() != 2:
            await self.channel_layer.group_send(
                self.room_name,
                {"type": "player_num", "objects": 1},
            )
            self.room_vars[self.room]["stop"] = True

            self.reset_board()
            
            #sends an update to the other player so that the board looks reset on the frontend
            await self.channel_layer.group_send(
                self.room_name,
                {"type": "state_update", "objects": list(self.room_vars[self.room]["players"].values())},
            )

        await self.check_full()
        # print("in consumer")

        await self.channel_layer.group_discard(self.room_name, self.channel_name)

        #deletes room if empty
        if len(self.room_vars[self.room]["players"]) == 0:
            await self.delete_room()
            async with self.update_lock:
                if self.room in self.room_vars:
                    del self.room_vars[self.room]

    #take a guess
    @database_sync_to_async
    def delete_room(self):
        Room.objects.filter(room_name=self.room).delete()

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message_type = text_data_json.get("type", "")

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
        await self.send(
            text_data=json.dumps(
                {
                    "type": "stateUpdate",
                    "objects": event["objects"],
                }
            )
        )

    async def sound(self, event):
        await self.send(
            text_data=json.dumps(
                {
                    "type": "sound",
                }
            )
        )

    async def player_num(self, event):
        await self.send(
            text_data=json.dumps(
                {
                    "type": "playerNum",
                    "num": event["objects"],
                }
            )
        )

    async def new_score(self, event):
        await self.send(
            text_data=json.dumps(
                {
                    "type": "score",
                    "objects": event["objects"],
                }
            )
        )

    async def game_loop_init(self):
        #waits for a second player to enter the room
        while self.room in self.room_vars and len(self.room_vars[self.room]["players"]) != 2:
            await asyncio.sleep(0.03)

        #tells the javascript side that another player has entered the room
        await self.send(
            text_data=json.dumps({"type": "playerNum", "num": 2})
        )
        
        #countdown at the start of the game
        a = time.time()
        while 1:
            b = time.time()
            b = 3 - math.floor(b - a)
            await self.send(
                text_data=json.dumps({"type": "countdown", "left": b})
            )
            if b == 0:
                break
            await asyncio.sleep(0.03)

        #checks if room still exists then launch the main game loop
        if self.room in self.room_vars:
            self.room_vars[self.room]["stop"] = False
            if self.room_vars[self.room]["players"][self.player_id]["side"] == "left":
                await self.game_loop()
            # game_loo = asyncio.create_task(self.game_loop())
            # else:
                # return

    async def game_loop(self):
        #initializes ball direction/position
        self.init_ball_values()
        self.ball_direction()

        #initialize fps restriction
        fpsInterval = 1.0 / 60.0
        then = asyncio.get_event_loop().time()

        #new variables are declared to hopefully reduce calculation time
        self.player1 = self.find_player("left")
        self.player2 = self.find_player("right")
        self.room_var = self.room_vars[self.room]
        # print("aaaa", len(asyncio.all_tasks()))

        #the main loop
        while len(self.room_var["players"]) == 2:
            #the 60 fps rule
            # now = asyncio.get_event_loop().time()
            # elapsed = now - then
            # if (elapsed > fpsInterval):
                # then = now - (elapsed % fpsInterval)

            #player movement
            async with self.update_lock:
                if self.player1["moveUp"]:
                    if self.player1["yPos"] - self.playerVelocity > 0:
                        self.player1["yPos"] -= self.playerVelocity
                    else:
                        self.player1["yPos"] = 0
                if self.player1["moveDown"]:
                    if self.player1["yPos"] + self.playerVelocity + self.player_height < self.board_height:
                        self.player1["yPos"] += self.playerVelocity
                    else:
                        self.player1["yPos"] = self.board_height - self.player_height
                
                if self.player2["moveUp"]:
                    if self.player2["yPos"] - self.playerVelocity > 0:
                        self.player2["yPos"] -= self.playerVelocity
                    else:
                        self.player2["yPos"] = 0
                if self.player2["moveDown"]:
                    if self.player2["yPos"] + self.playerVelocity + self.player_height < self.board_height:
                        self.player2["yPos"] += self.playerVelocity
                    else:
                        self.player2["yPos"] = self.board_height - self.player_height

            #calculate ball collisions
            self.calculate_ball_changes()

            #if == True, tells the javascript to play a sound
            if self.bounce:
                self.bounce = False
                await self.channel_layer.group_send(
                    self.room_name,
                    {"type": "sound"},
                )

            #if != 0, tells the player has scored
            if self.score:
                if self.score == 1:
                    await self.channel_layer.group_send(
                        self.room_name,
                        {"type": "new_score", "objects": {"player": 1, "score": self.player1["score"]}},
                    )
                elif self.score == 2:
                    await self.channel_layer.group_send(
                        self.room_name,
                        {"type": "new_score", "objects": {"player": 2, "score": self.player2["score"]}},
                    )
                self.score = 0

            #ball movement
            # if self.room_var["players"][self.player_id]["side"] == "left":
            self.room_var["ball_xPos"] += self.room_var["ball_velocityX"]
            self.room_var["ball_yPos"] += self.room_var["ball_velocityY"]
            
            #the main json sent to the javascript with the players pos as well as ball pos
            # if self.room_var["players"][self.player_id]["side"] == "left":
            await self.channel_layer.group_send(
                self.room_name,
                {"type": "state_update", "objects": {"player1Pos": self.player1["yPos"], "player2Pos": self.player2["yPos"], "ball_yPos": self.room_var["ball_yPos"], "ball_xPos": self.room_var["ball_xPos"]}},
            )
            # await self.send(
            #     text_data=json.dumps({"type": "stateUpdate", "objects": {"player1Pos": self.player1["yPos"], "player2Pos": self.player2["yPos"], "ball_yPos": self.room_var["ball_yPos"], "ball_xPos": self.room_var["ball_xPos"]}})
            # )

            #gives time to the rest of the processes to operate
            await asyncio.sleep(1 / 60)

    #most of the game logic/calculations are here
    def calculate_ball_changes(self):

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
            if (self.room_var["stop"] == False and ball_yPos + ball_velocityY + self.ball_height + 2 >= self.player2["yPos"] and ball_yPos + ball_velocityY - 2 <= self.player2["yPos"] + self.player_height):
                ball_velocityY = ((ball_yPos + self.ball_height / 2) - (self.player2["yPos"] + self.player_height / 2)) / 7
                ball_velocityX *= -1
                if ball_velocityX < 0:
                    ball_velocityX -= 0.5
                else:
                    ball_velocityX += 0.5

                self.bounce = True

        #checks if the ball hit the left paddle
        if (ball_xPos + ball_velocityX <= 11):
            if (self.room_var["stop"] == False and ball_yPos + ball_velocityY + self.ball_height + 2 >= self.player1["yPos"] and ball_yPos + ball_velocityY - 2 <= self.player1["yPos"] + self.player_height):
                ball_velocityY = ((ball_yPos + self.ball_height / 2) - (self.player1["yPos"] + self.player_height / 2)) / 7
                ball_velocityX *= -1
                if (ball_velocityX < 0):
                    ball_velocityX -= 0.5
                else:
                    ball_velocityX += 0.5

                self.bounce = True

        #checks if a player has scored
        if (ball_xPos + ball_velocityX < 0 or ball_xPos + ball_velocityX + self.ball_width > self.board_width):
            if (self.room_var["stop"] == False and ball_xPos + ball_velocityX < 0):
                self.player2["score"] += 1
                self.score = 2
            elif self.room_var["stop"] == False:
                self.player1["score"] += 1
                self.score = 1
        
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
