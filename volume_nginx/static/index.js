//const ws = new WebSocket("ws://10.19.246.185:8000/ws/notification/room/");

var player_id = 0;
//board
let board_height = 800;
let board_width = 1200;

//player
let player_width = 15;
let player_height = 100;
let playerVelocity = 0;

//balling
let ball_width = 15;
let ball_height = 15;
let ball_velocity = 10;

let ball = {
    width: ball_width,
    height: ball_height,
    xPos: (board_width / 2) - (ball_width / 2),
    yPos: (board_height / 2) - (ball_height / 2),
    velocityY: 0,
    velocityX: 0,
    velocityXTmp: 0,
    velocityYTmp: 0,
}

let player1 = {
    xPos: 10,
    yPos: board_height / 2 - player_height / 2,
    width: player_width,
    height: player_height,
    velocityY: playerVelocity,
    score: 0,
    prediction: -1,
}

let player2 = {
    xPos: board_width - player_width - 10,
    yPos: board_height / 2 - player_height / 2,
    width: player_width,
    height: player_height,
    velocityY: playerVelocity,
    score: 0,
    prediction: -1,
}

var stop = false;
var gameMod = 0;
var sound = false;
var animation_id = -1;
var isalone = true;
var time_left = 0;

function reset_board() {
    gameMod = 0;
    player2.xPos = board_width - player_width - 10;
    player2.yPos = board_height / 2 - player_height / 2;
    player2.width = player_width;
    player2.height = player_height;
    player2.velocityY = playerVelocity;
    //player2.score = 0;
    player2.prediction = -1;
    player1.xPos = 10;
    player1.yPos = board_height / 2 - player_height / 2;
    player1.width = player_width;
    player1.height = player_height;
    player1.velocityY = playerVelocity;
    //player1.score = 0;
    player1.prediction = -1;
    ball.width = ball_width;
    ball.height = ball_height;
    ball.xPos = (board_width / 2) - (ball_width / 2);
    ball.yPos = (board_height / 2) - (ball_height / 2);
    ball.velocityY = 0;
    ball.velocityX = 0;
    ball.velocityXTmp = 0;
    ball.velocityYTmp = 0;
}

function sound_change() {
    if (sound == false)
        sound = true;
    else
        sound = false;
}

function stop_playing() {
    reset_board();
    if (stop == false) {
        player1.score = 0;
        player2.score = 0;
    }
    //window.cancelAnimationFrame(animation_id);
}

var fpsInterval;
var then;

function startAnimating(fps) {
    fpsInterval = 1000 / fps;
    then = performance.now();
    gameLoop();
}

window.onload = function () {
    let board = document.getElementById("board");
    board.width = board_width;
    board.height = board_height;
    context = board.getContext("2d");

    document.addEventListener("keydown", movePlayer);
    document.addEventListener("keyup", stopPlayer);
    draw_board();
    gameLoop();
}

function draw_board()
{
    context.fillStyle = "white";
    //player 1
    context.fillRect(player1.xPos, player1.yPos, player1.width, player1.height);

    //player 2
    context.fillRect(player2.xPos, player2.yPos, player2.width, player2.height);

    //middle_line
    fill_middle_lines();

    //score
    context.font = "48px serif";
    context.fillText(player1.score, 100, 50);

    context.fillText(player2.score, board_width - 130, 50);

    //ball
    context.fillStyle = "white";
    context.fillRect(ball.xPos, ball.yPos, ball.width, ball.height);

}

var trigger = true;

function gameLoop() {
    animation_id = window.requestAnimationFrame(gameLoop);

    context.clearRect(0, 0, board.width, board.height);
    // let now = performance.now();
    // let elapsed = now - then;

    //if (elapsed > fpsInterval && stop == false)
    if (stop == false) {
        //then = now - (elapsed % fpsInterval);
        draw_board();
    }
    if (isalone == true)
    {
        context.fillStyle = "white";
        context.fillText("waiting for a second player", 325, 315);
    }
    if (player1.score == 5)
    {
        if (trigger == true)
        {
            setTimeout(() => { location.replace("https://" + window.location.host); }, 5000);
            trigger = false;
        }
        context.font = "100px serif";
        context.fillText("Player 1 won !", 330, 400);
    }
    else if (player2.score == 5)
    {
        if (trigger == true)
        {
            setTimeout(() => { location.replace("https://" + window.location.host); }, 5000);
            trigger = false;
        }
        context.font = "100px serif";
        context.fillText("Player 2 won !", 330, 400);
    }
    if (time_left != 0)
    {
        context.fillStyle = "red";
        context.font = "100px serif";
        context.fillText(time_left, 575, 190);
    }
    //window.cancelAnimationFrame(animation_id);
}

function fill_middle_lines() {
    for (let i = 0; i < board_height; i += 4.2) {
        context.fillStyle = "gray";
        context.fillRect(board_width / 2 - 5, i, 10, 30);
        i += 60;
    }
}

function play() {
    if (sound == true)
        audio.play();
}

var lastSent = "none";

function movePlayer(e) {
    if (e.key == 'w' && lastSent != "keyW") {
        ws.send(JSON.stringify({ type: "keyW", playerId: player_id }));
        lastSent = "keyW";
    }
    if (e.key == 's' && lastSent != "keyS") {
        ws.send(JSON.stringify({ type: "keyS", playerId: player_id }));
        lastSent = "keyS"
    }
}

//allows the player to stop if key is released
function stopPlayer(e) {
    if (e.key == 'w' && lastSent != "keyStop") {
        ws.send(JSON.stringify({ type: "keyStop", playerId: player_id }));
        lastSent = "keyStop"
    }
    if (e.key == 's' && lastSent != "keyStop") {
        ws.send(JSON.stringify({ type: "keyStop", playerId: player_id }));
        lastSent = "keyStop"
    }
}

ws.addEventListener("message", event => {
    let messageData = JSON.parse(event.data);
    // console.log(messageData);
    if (messageData.type === "stateUpdate") {
        for (o = 0; o < messageData.objects.length; o++)
        {
            if (messageData.objects[o].side == "left")
            {
                player1.yPos = messageData.objects[o].yPos;
                player1.score = messageData.objects[o].score;
                ball.yPos = messageData.objects[o].ballY;
                ball.xPos = messageData.objects[o].ballX;
            }
            else
            {
                player2.yPos = messageData.objects[o].yPos;
                player2.score = messageData.objects[o].score;
                ball.yPos = messageData.objects[o].ballY;
                ball.xPos = messageData.objects[o].ballX;
            }
        }
    }
    else if (messageData.type === "playerId") {
        player_id = messageData.playerId;
    }
    else if (messageData.type === "playerNum") {
        if (messageData.num === 2)
            isalone = false;
        else if (messageData.num === 1)
            isalone = true;
    }
    else if (messageData.type === "sound") {
        play();
    }
    else if (messageData.type === "countdown") {
        time_left = messageData.left;
    }
    if (messageData.type != "stateUpdate")
        console.log(messageData);
});