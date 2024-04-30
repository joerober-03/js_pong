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
# from channels.exceptions import StopConsumer


class ChatConsumer(AsyncWebsocketConsumer):
    # p_id = 0

    #board
    board_height = 800
    board_width = 1200

    #player
    player_width = 15
    player_height = 100
    playerVelocityUp = -20
    playerVelocityDown = 20

    #balling
    ball_width = 15
    ball_height = 15
    ball_velocity = 10

    # class Players:
    #     player_id = 0
    #     xPos = (board_width / 2) - (ball_width / 2)
    #     yPos = (board_height / 2) - (ball_height / 2)
    #     velocityX = 0
    #     velocityY = 0
    #     score = 0
    

    isalone = {
        "num" : 0,
    }

    #ball = Ball()

    stop = False

    players = {}
    balls = {}

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

        ball = self.find_ball(self.room)
        self.ball_id = str(uuid.uuid4())
        if ball:
            self.ball_id = ball["id"]
        else:
            async with self.update_lock:
                self.balls[self.ball_id] = {
                    "width" : self.ball_width,
                    "height" : self.ball_height,
                    "xPos" : (self.board_width / 2) - (self.ball_width / 2),
                    "yPos" : (self.board_height / 2) - (self.ball_height / 2),
                    "velocityY" : 0,
                    "velocityX" : 0,
                    "room": self.room,
                    "id": self.ball_id,
                }

        if await self.assign_player_id() == 0:
            async with self.update_lock:
                self.players[self.player_id] = {
                    "id": self.player_id,
                    "side": "left",
                    "room": self.room,
                    "xPos": 10,
                    "yPos": self.board_height / 2 - self.player_height / 2,
                    "width": self.player_width,
                    "height": self.player_height,
                    "velocityY": 0,
                    "score": 0,
                    "moveUp": False,
                    "moveDown": False,
                    "ballX": 0,
                    "ballY": 0,
                }
        else:
            async with self.update_lock:
                self.players[self.player_id] = {
                    "id": self.player_id,
                    "side": "right",
                    "room": self.room,
                    "xPos": self.board_width - self.player_width - 10,
                    "yPos": self.board_height / 2 - self.player_height / 2,
                    "width": self.player_width,
                    "height": self.player_height,
                    "velocityY": 0,
                    "score": 0,
                    "moveUp": False,
                    "moveDown": False,
                    "ballX": 0,
                    "ballY": 0,
                }
        
        init = asyncio.create_task(self.game_loop_init())

    @database_sync_to_async
    def assign_player_id(self):
        current_room = Room.objects.get(room_name=self.room)
        if current_room.left == False:
            Room.objects.filter(room_name=self.room).update(left=True)
            return 0
        else:
            Room.objects.filter(room_name=self.room).update(right=True)
            return 1
        return 2
        
    async def disconnect(self, close_code):
        self.stop = True
    
        del_ball = False

        del_ball = await self.remove_player_id()

        async with self.update_lock:
            if self.player_id in self.players:
                del self.players[self.player_id]

        async with self.update_lock:
            if self.ball_id in self.balls and del_ball == True:
                del self.balls[self.ball_id]

        await self.channel_layer.group_discard(self.room_name, self.channel_name)
        # raise StopConsumer()

    @database_sync_to_async
    def remove_player_id(self):
        if self.players[self.player_id]["side"] == "left":
            Room.objects.filter(room_name=self.room).update(left=False)
        else:
            Room.objects.filter(room_name=self.room).update(right=False)
        
        current_room = Room.objects.get(room_name=self.room)
        if current_room.left == False and current_room.right == False:
            return True
        return False

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message_type = text_data_json.get("type", "")

        player_id = text_data_json["playerId"]

        player = self.players.get(player_id, None)
        if not player:
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
        while await self.check_room() == 0:
            if self.stop:
                break
        
        if self.stop == False:
            self.isalone["num"] = 2

            await self.channel_layer.group_send(
                    self.room_name,
                    {"type": "player_num", "objects": self.isalone},
                )
            
            game = asyncio.create_task(self.game_loop())

    async def game_loop(self):
        self.init_ball_values()
        self.ball_direction()
        while self.stop == False:
            async with self.update_lock:
                # print("this is room " + self.room)
                # print(len(self.players))
                for player in self.players.values():
                    # print(player["room"])
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

            ball = self.find_ball(self.room)
            ball["xPos"] += ball["velocityX"]
            ball["yPos"] += ball["velocityY"]
            
            for player in self.players.values():
                player["ballX"] = ball["xPos"]
                player["ballY"] = ball["yPos"]
            
            await self.channel_layer.group_send(
                self.room_name,
                {"type": "state_update", "objects": list(self.players.values())},
            )

            # await self.send(text_data=json.dumps({"type": "state_update", "objects": list(self.players.values())},))

            # await self.channel_layer.group_send(
            #     self.room_name,
            #     {"type": "ball_update"z, "objects": list(self.ball.values())},
            # )

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

        player1 = self.find_player("left", self.room)
        player2 = self.find_player("right", self.room)

        ball = self.find_ball(self.room)

        if (ball["yPos"] + ball["velocityY"] < 0 or ball["yPos"] + ball["velocityY"] + ball["height"] > self.board_height):
            ball["velocityY"] *= -1

        if (ball["xPos"] + ball["velocityX"] + ball["width"] >= self.board_width - 11):
            if (ball["yPos"] + ball["velocityY"] + ball["height"] + 2 >= player2["yPos"] and ball["yPos"] + ball["velocityY"] - 2 <= player2["yPos"] + player2["height"]):
                ball["velocityY"] = ((ball["yPos"] + ball["height"] / 2) - (player2["yPos"] + player2["height"] / 2)) / 7
                ball["velocityX"] *= -1
                if ball["velocityX"] < 0:
                    ball["velocityX"] -= 0.5
                else:
                    ball["velocityX"] += 0.5

        if (ball["xPos"] + ball["velocityX"] <= 11):
            if (ball["yPos"] + ball["velocityY"] + ball["height"] + 2 >= player1["yPos"] and ball["yPos"] + ball["velocityY"] - 2 <= player1["yPos"] + player1["height"]):
                ball["velocityY"] = ((ball["yPos"] + ball["height"] / 2) - (player1["yPos"] + player1["height"] / 2)) / 7
                ball["velocityX"] *= -1
                if (ball["velocityX"] < 0):
                    ball["velocityX"] -= 0.5
                else:
                    ball["velocityX"] += 0.5

        if (ball["xPos"] + ball["velocityX"] < 0 or ball["xPos"] + ball["velocityX"] + ball["width"] > self.board_width):
            if (ball["xPos"] + ball["velocityX"] < 0):
                player2["score"] += 1
            else:
                player1["score"] += 1
            
            self.init_ball_values()
            self.ball_direction()
            
    def ball_direction(self):
        ball = self.find_ball(self.room)
        r1 = random.randint(0, 1)
        if r1 == 0:
            r1 = self.ball_velocity
        else:
            r1 = self.ball_velocity * -1
        
        r2 = 0
        while r2 == 0:
            r2 = random.randint(-5, 5)

        ball["velocityY"] = 0
        ball["velocityX"] = 0

        r = Timer(1.0, self.assign_values, (1, r2))
        s = Timer(1.0, self.assign_values, (0, r1))

        r.start()
        s.start()

    def assign_values(self, id, value):
        ball = self.find_ball(self.room)
        if id == 0:
            ball["velocityX"] = value
        else:
            ball["velocityY"] = value

    def init_ball_values(self):
        ball = self.find_ball(self.room)
        ball["width"] = self.ball_width
        ball["height"] = self.ball_height
        ball["xPos"] = (self.board_width / 2) - (self.ball_width / 2)
        ball["yPos"] = (self.board_height / 2) - (self.ball_height / 2)
        ball["velocityY"] = 0
        ball["velocityX"] = 0

    def find_player(self, target_side, target_room):
        for player in self.players.values():
            if player["side"] == target_side and player["room"] == target_room:
                return player
        return None

    def find_ball(self, target_room):
        for ball in self.balls.values():
            if ball["room"] == target_room:
                return ball
        return None
