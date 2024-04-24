import json
import sys
import uuid
import asyncio
import math
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from chat.models import *
from asgiref.sync import async_to_sync

class ChatConsumer(AsyncWebsocketConsumer):
    p_id = 0
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

    test = 0

    # class Players:
    #     player_id = 0
    #     xPos = (board_width / 2) - (ball_width / 2)
    #     yPos = (board_height / 2) - (ball_height / 2)
    #     velocityX = 0
    #     velocityY = 0
    #     score = 0
    
    # class Ball:
    #     width = ball_width
    #     height = ball_height
    #     xPos = 10
    #     yPos = board_height / 2 - player_height / 2
    #     velocityY: 0
    #     velocityX: 0

    players = {}
    update_lock = asyncio.Lock()

    async def connect(self):
        #self.player_id = str(uuid.uuid4())
        self.player_id = self.p_id
        self.p_id += 1
        self.room_name = f"room_{self.scope['url_route']['kwargs']['room_name']}"
        await self.channel_layer.group_add(self.room_name, self.channel_name)
        await self.accept()

        await self.send(
            text_data=json.dumps({"type": "playerId", "playerId": self.player_id})
        )
        if (self.player_id % 2) == 0:
        #     print("a")
            async with self.update_lock:
                self.players[self.player_id] = {
                    "id": self.player_id,
                    "xPos": 10,
                    "yPos": self.board_height / 2 - self.player_height / 2,
                    "width": self.player_width,
                    "height": self.player_height,
                    "velocityY": 0,
                    "score": 0,
                    "moveUp": False,
                    "moveDown": False,
                }
        else:
            print("b")
            async with self.update_lock:
                self.players[self.player_id] = {
                    "id": self.player_id,
                    "xPos": self.board_width - self.player_width - 10,
                    "yPos": self.board_height / 2 - self.player_height / 2,
                    "width": self.player_width,
                    "height": self.player_height,
                    "velocityY": 0,
                    "score": 0,
                    "moveUp": False,
                    "moveDown": False,
                }

        # if len(self.players) == 1:
        #     await self.send(
        #     text_data=json.dumps({"type": "isAlone", "isAlone": True})
        # )
        
        #print(len(self.players))
        #if len(self.players) == 2:
        test = asyncio.create_task(self.game_loop())

        
    async def disconnect(self, close_code):
        async with self.update_lock:
            if self.player_id in self.players:
                del self.players[self.player_id]

        await self.channel_layer.group_discard(self.room_name, self.channel_name)

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

    async def game_loop(self):
        # print("v")
        while len(self.players) > 0:
            print(self.test)
            self.test += 1
            #print(len(self.players))
            async with self.update_lock:
                for player in self.players.values():
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


            await self.channel_layer.group_send(
                self.room_name,
                {"type": "state_update", "objects": list(self.players.values())},
            )
            await asyncio.sleep(0.02)
        
