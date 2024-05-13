import json
import random
import sys
import uuid
import asyncio
import math
import time
from threading import Timer
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from chat.models import *
from asgiref.sync import async_to_sync

class ChatConsumer(AsyncWebsocketConsumer):

    #board
    board_height = 800
    board_width = 1200

    #player
    player_width = 15
    player_height = 100
    playerVelocityUp = -10
    playerVelocityDown = 10

    #balling
    ball_width = 15
    ball_height = 15
    ball_velocity = 10

    bounce = False

    room_vars = {}

    update_lock = asyncio.Lock()

    async def connect(self):
        self.room = f"{self.scope['url_route']['kwargs']['room_name']}"
        self.player_id = str(uuid.uuid4())
        self.room_name = f"room_{self.scope['url_route']['kwargs']['room_name']}"
        await self.channel_layer.group_add(self.room_name, self.channel_name)
        await self.accept()

        await self.send(
            text_data=json.dumps({"type": "playerId", "playerId": self.player_id})
        )

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
                    "ballX": 0,
                    "ballY": 0,
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
                    "ballX": 0,
                    "ballY": 0,
                }
        else:
            return

        await self.check_full()

        init = asyncio.create_task(self.game_loop_init())

    @database_sync_to_async
    def check_full(self):
        if self.assign_player_side() == 2:
            Room.objects.filter(room_name=self.room).update(full=True)
        else:
            Room.objects.filter(room_name=self.room).update(full=False)

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
        print("in consumer")
        async with self.update_lock:
            if self.player_id in self.room_vars[self.room]["players"]:
                del self.room_vars[self.room]["players"][self.player_id]

        if self.assign_player_side() != 2:
            await self.channel_layer.group_send(
                self.room_name,
                {"type": "player_num", "objects": 1},
            )
            self.room_vars[self.room]["stop"] = True

            self.reset_board()
            
            await self.channel_layer.group_send(
                self.room_name,
                {"type": "state_update", "objects": list(self.room_vars[self.room]["players"].values())},
            )

        await self.check_full()
        # print("in consumer")

        await self.channel_layer.group_discard(self.room_name, self.channel_name)

        if len(self.room_vars[self.room]["players"]) == 0:
            await self.delete_room()
            async with self.update_lock:
                if self.room in self.room_vars:
                    del self.room_vars[self.room]

    @database_sync_to_async
    def delete_room(self):
        Room.objects.filter(room_name=self.room).delete()

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message_type = text_data_json.get("type", "")

        player_id = text_data_json["playerId"]

        player = self.room_vars[self.room]["players"].get(player_id, None)
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
                    "objects": event["objects"],
                }
            )
        )

    async def player_num(self, event):
        await self.send(
            text_data=json.dumps(
                {
                    "type": "playerNum",
                    "objects": event["objects"],
                }
            )
        )

    async def game_loop_init(self):
        while self.room in self.room_vars and self.player_id in self.room_vars[self.room]["players"]:
            while self.room in self.room_vars and len(self.room_vars[self.room]["players"]) != 2:
                await asyncio.sleep(0.03)
            await self.send(
                text_data=json.dumps({"type": "playerNum", "num": 2})
            )

            if self.room in self.room_vars:
                self.room_vars[self.room]["stop"] = False
                await self.game_loop()
            await asyncio.sleep(0.03)

    async def game_loop(self):
        self.init_ball_values()
        self.ball_direction()
        fpsInterval = 1.0 / 60.0
        then = time.time()
        while len(self.room_vars[self.room]["players"]) == 2:
            now = time.time()
            elapsed = now - then
            if (elapsed > fpsInterval):
                then = now - (elapsed % fpsInterval)
                print(len(asyncio.all_tasks()))
                async with self.update_lock:
                    for player in self.room_vars[self.room]["players"].values():
                        if player["moveUp"]:
                            if player["yPos"] + self.playerVelocityUp > 0:
                                player["yPos"] += self.playerVelocityUp
                            else:
                                player["yPos"] = 0
                            
                        if player["moveDown"]:
                            if player["yPos"] + self.playerVelocityDown + self.player_height < self.board_height:
                                player["yPos"] += self.playerVelocityDown
                            else:
                                player["yPos"] = self.board_height - self.player_height

                self.calculate_ball_changes()

                if (self.bounce == True):
                    self.bounce = False
                    await self.channel_layer.group_send(
                        self.room_name,
                        {"type": "sound", "objects": 1},
                    )

                self.room_vars[self.room]["ball_xPos"] += self.room_vars[self.room]["ball_velocityX"]
                self.room_vars[self.room]["ball_yPos"] += self.room_vars[self.room]["ball_velocityY"]
                
                for player in self.room_vars[self.room]["players"].values():
                    player["ballX"] = self.room_vars[self.room]["ball_xPos"]
                    player["ballY"] = self.room_vars[self.room]["ball_yPos"]

                await self.channel_layer.group_send(
                    self.room_name,
                    {"type": "state_update", "objects": list(self.room_vars[self.room]["players"].values())},
                )

                await asyncio.sleep(0.03)

    @database_sync_to_async
    def check_room(self):
        current_room = Room.objects.get(room_name=self.room)
        if current_room.left == True and current_room.right == True:
            return 1
        else:
            return 0
        return 2

    def calculate_ball_changes(self):

        player1 = self.find_player("left")
        player2 = self.find_player("right")

        if (not player1 or not player2):
            return

        if (self.room_vars[self.room]["ball_yPos"] + self.room_vars[self.room]["ball_velocityY"] < 0 or self.room_vars[self.room]["ball_yPos"] + self.room_vars[self.room]["ball_velocityY"] + self.ball_height > self.board_height):
            self.room_vars[self.room]["ball_velocityY"] *= -1

        if (self.room_vars[self.room]["ball_xPos"] + self.room_vars[self.room]["ball_velocityX"] + self.ball_width >= self.board_width - 11):
            if (self.room_vars[self.room]["stop"] == False and self.room_vars[self.room]["ball_yPos"] + self.room_vars[self.room]["ball_velocityY"] + self.ball_height + 2 >= player2["yPos"] and self.room_vars[self.room]["ball_yPos"] + self.room_vars[self.room]["ball_velocityY"] - 2 <= player2["yPos"] + self.player_height):
                self.room_vars[self.room]["ball_velocityY"] = ((self.room_vars[self.room]["ball_yPos"] + self.ball_height / 2) - (player2["yPos"] + self.player_height / 2)) / 7
                self.room_vars[self.room]["ball_velocityX"] *= -1
                if self.room_vars[self.room]["ball_velocityX"] < 0:
                    self.room_vars[self.room]["ball_velocityX"] -= 0.5
                else:
                    self.room_vars[self.room]["ball_velocityX"] += 0.5

                self.bounce = True

        if (self.room_vars[self.room]["ball_xPos"] + self.room_vars[self.room]["ball_velocityX"] <= 11):
            if (self.room_vars[self.room]["stop"] == False and self.room_vars[self.room]["ball_yPos"] + self.room_vars[self.room]["ball_velocityY"] + self.ball_height + 2 >= player1["yPos"] and self.room_vars[self.room]["ball_yPos"] + self.room_vars[self.room]["ball_velocityY"] - 2 <= player1["yPos"] + self.player_height):
                self.room_vars[self.room]["ball_velocityY"] = ((self.room_vars[self.room]["ball_yPos"] + self.ball_height / 2) - (player1["yPos"] + self.player_height / 2)) / 7
                self.room_vars[self.room]["ball_velocityX"] *= -1
                if (self.room_vars[self.room]["ball_velocityX"] < 0):
                    self.room_vars[self.room]["ball_velocityX"] -= 0.5
                else:
                    self.room_vars[self.room]["ball_velocityX"] += 0.5

                self.bounce = True

        if (self.room_vars[self.room]["ball_xPos"] + self.room_vars[self.room]["ball_velocityX"] < 0 or self.room_vars[self.room]["ball_xPos"] + self.room_vars[self.room]["ball_velocityX"] + self.ball_width > self.board_width):
            if (self.room_vars[self.room]["stop"] == False and self.room_vars[self.room]["ball_xPos"] + self.room_vars[self.room]["ball_velocityX"] < 0):
                player2["score"] += 1
            elif self.room_vars[self.room]["stop"] == False:
                player1["score"] += 1
            
            self.init_ball_values()
            self.ball_direction()
            
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

        r = Timer(1.0, self.assign_values, (1, r2))
        s = Timer(1.0, self.assign_values, (0, r1))

        r.start()
        s.start()

    def assign_values(self, id, value):
        if id == 0:
            self.room_vars[self.room]["ball_velocityX"] = value
        else:
            self.room_vars[self.room]["ball_velocityY"] = value

    def init_ball_values(self):
        self.room_vars[self.room]["ball_xPos"] = (self.board_width / 2) - (self.ball_width / 2)
        self.room_vars[self.room]["ball_yPos"] = (self.board_height / 2) - (self.ball_height / 2)
        self.room_vars[self.room]["ball_velocityY"] = 0
        self.room_vars[self.room]["ball_velocityX"] = 0

    def find_player(self, target_side):
        for player in self.room_vars[self.room]["players"].values():
            if player["side"] == target_side:
                return player
        return None

    def reset_board(self):
        self.init_ball_values
        for player in self.room_vars[self.room]["players"].values():
            player["yPos"] = self.board_height / 2 - self.player_height / 2
            player["score"] = 0
            player["ballX"] = 0
            player["ballY"] = 0
            player["ballX"] = (self.board_width / 2) - (self.ball_width / 2)
            player["ballY"] = (self.board_height / 2) - (self.ball_height / 2)
