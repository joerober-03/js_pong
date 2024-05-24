
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

state_update = {
    "player1Pos": board_height / 2 - player_height / 2,
    "player2Pos": board_height / 2 - player_height / 2,
    "ball_yPos": (board_height / 2) - (ball_height / 2),
    "ball_xPos": (board_width / 2) - (ball_width / 2),
    "player1Score": 0,
    "player2Score": 0,
    "sound": True,
    }

room_vars = {}