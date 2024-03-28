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

var stop = true;
var gameMod = 0;
var sound = false;
var animation_id = -1;

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

function button1Init() {
    reset_board();
    player1.score = 0;
    player2.score = 0;
    gameMod = 1;
    stop = false;
    window.cancelAnimationFrame(animation_id);
    gameloopInit();
    //startAnimating(60);
    gameLoop();
}

function button2Init() {
    reset_board();
    player1.score = 0;
    player2.score = 0;
    gameMod = 2;
    stop = false;
    window.cancelAnimationFrame(animation_id);
    gameloopInit();
    //startAnimating(60);
    gameLoop();
}

function button3Init() {
    reset_board();
    player1.score = 0;
    player2.score = 0;
    gameMod = 3;
    stop = false;
    window.cancelAnimationFrame(animation_id);
    gameloopInit();
    //startAnimating(60);
    gameLoop();
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

function gameloopInit() {
    let ran = Math.floor(Math.random() * 2);
    let tmp = ball_velocity;
    let tmp2 = 0;
    while (tmp2 == 0)
        tmp2 = Math.floor(Math.random() * 11) - 5;
    ball.velocityY = tmp2;
    if (ran == 0) {
        tmp *= -1;
    }
    ball.velocityX = tmp;
    if (ran == 0 && gameMod == 3)
        makeBot1Prediction();
    else if (ran == 1 && (gameMod == 1 || gameMod == 3))
        makeBot2Prediction();
    ball.velocityX = 0;
    ball.velocityY = 0;
    setTimeout(() => { ball.velocityY = tmp2; }, 500);
    setTimeout(() => { ball.velocityX = tmp; }, 500);
    document.addEventListener("keydown", movePlayer);
    document.addEventListener("keyup", stopPlayer);
}

function gameLoop() {
    animation_id = window.requestAnimationFrame(gameLoop);

    // let now = performance.now();
    // let elapsed = now - then;

    //if (elapsed > fpsInterval && stop == false)
    if (stop == false) {
        //then = now - (elapsed % fpsInterval);

        context.fillStyle = "white";
        context.clearRect(0, 0, board.width, board.height);
        //bot1 movement
        if (gameMod == 3) {
            if (player1.prediction >= player1.yPos && player1.prediction <= player1.yPos + player1.height || player1.prediction == -1)
                player1.velocityY = 0;
            else {
                if (player1.yPos + player1.height < player1.prediction)
                    player1.velocityY = 10;
                if (player1.yPos > player1.prediction)
                    player1.velocityY = -10;
            }
        }

        //player 1
        if (player1.yPos + player1.velocityY > 0 && player1.yPos + player1.velocityY + player1.height < board_height)
            player1.yPos += player1.velocityY;
        else if (!(player1.yPos + player1.velocityY > 0))
            player1.yPos = 2;
        else
            player1.yPos = board_height - player1.height - 2;
        context.fillRect(player1.xPos, player1.yPos, player1.width, player1.height);

        //bot2 movement
        if (gameMod == 1 || gameMod == 3) {
            if (player2.prediction >= player2.yPos && player2.prediction <= player2.yPos + player2.height || player2.prediction == -1)
                player2.velocityY = 0;
            else {
                if (player2.yPos + player2.height < player2.prediction)
                    player2.velocityY = 10;
                if (player2.yPos > player2.prediction)
                    player2.velocityY = -10;
            }
        }

        //player 2
        if (player2.yPos + player2.velocityY > 0 && player2.yPos + player2.velocityY + player2.height < board_height)
            player2.yPos += player2.velocityY;
        else if (!(player2.yPos + player2.velocityY > 0))
            player2.yPos = 2;
        else
            player2.yPos = board_height - player2.height - 2;
        context.fillRect(player2.xPos, player2.yPos, player2.width, player2.height);

        //middle_line
        fill_middle_lines();

        //ball
        changeBallVelocity();

        //score
        context.font = "48px serif";
        context.fillText(player1.score, 100, 50);

        context.fillText(player2.score, board_width - 130, 50);
        if (stop == false) {
            ball.xPos += ball.velocityX;
            ball.yPos += ball.velocityY;
            context.fillStyle = "white";
            context.fillRect(ball.xPos, ball.yPos, ball.width, ball.height);
        }
        if (stop == true) {
            player1.score = 0;
            player2.score = 0;
        }
    }
}

function fill_middle_lines() {
    for (let i = 0; i < board_height; i += 4.2) {
        context.fillStyle = "gray";
        context.fillRect(board_width / 2 - 5, i, 10, 30);
        i += 60;
    }
}

function changeBallVelocity() {
    if (!(ball.yPos + ball.velocityY > 0 && ball.yPos + ball.velocityY + ball.height < board_height)) {
        ball.velocityY *= -1;
    }
    if (ball.xPos + ball.velocityX + ball.width >= board_width - 11) {
        if (ball.yPos + ball.velocityY + ball.height + 2 >= player2.yPos && ball.yPos + ball.velocityY - 2 <= player2.yPos + player2.height) {
            ball.velocityY = ((ball.yPos + ball.height / 2) - (player2.yPos + player2.height / 2)) / 7;
            ball.velocityX *= -1;
            if (ball.velocityX < 0)
                ball.velocityX -= 0.5;
            else
                ball.velocityX += 0.5;
            if (gameMod == 3)
                makeBot1Prediction();
            if (sound == true)
                play();
        }
    }
    if (ball.xPos + ball.velocityX <= 11) {
        if (ball.yPos + ball.velocityY + ball.height + 2 >= player1.yPos && ball.yPos + ball.velocityY - 2 <= player1.yPos + player1.height) {
            ball.velocityY = ((ball.yPos + ball.height / 2) - (player1.yPos + player1.height / 2)) / 7;
            ball.velocityX *= -1;
            if (ball.velocityX < 0)
                ball.velocityX -= 0.5;
            else
                ball.velocityX += 0.5;
            if (gameMod == 1 || gameMod == 3)
                makeBot2Prediction();
            //setTimeout(() => { makeBot2Prediction(); }, 500);
            if (sound == true)
                play();
        }
    }
    if (!(ball.xPos + ball.velocityX > 0 && ball.xPos + ball.velocityX + ball.width < board_width)) {
        context.fillStyle = "white";
        if (!(ball.xPos + ball.velocityX > 0))
            player2.score++;
        else
            player1.score++;

        if (player1.score == 5) {
            stop_playing();
            context.font = "100px serif";
            context.fillText("Player 1 won !", 325, 400);
            stop = true;
            return;
        }
        if (player2.score == 5) {
            stop_playing();
            context.font = "100px serif";
            context.fillText("Player 2 won !", 330, 400);
            stop = true;
            return;
        }
        ball.xPos = (board_width / 2) - (ball_width / 2);
        ball.yPos = (board_height / 2) - (ball_height / 2);
        let ran = Math.floor(Math.random() * 2);
        ball.velocityX = ball_velocity;
        ball.velocityY = 0;
        while (ball.velocityY == 0)
            ball.velocityY = Math.floor(Math.random() * 11) - 5;
        if (ran == 0)
            ball.velocityX *= -1;
        if (gameMod == 4) {
            ws.send(JSON.stringify(ball));
        }
        if (ball.velocityX > 0 && (gameMod == 1 || gameMod == 3))
            makeBot2Prediction();
        else if (ball.velocityX < 0 && gameMod == 3)
            makeBot1Prediction();
        ball.velocityXTmp = ball.velocityX;
        ball.velocityYTmp = ball.velocityY;
        ball.velocityX = 0;
        ball.velocityY = 0;
        setTimeout(() => { ball.velocityY = ball.velocityYTmp; }, 500);
        setTimeout(() => { ball.velocityX = ball.velocityXTmp; }, 500);
    }
}

function movePlayer(e) {

    if (gameMod == 1 || gameMod == 2) {
        if (e.key == 'w') {
            player1.velocityY = -10;
        }
        if (e.key == 's') {
            player1.velocityY = 10;
        }
    }
    if (gameMod == 2) {
        if (e.key == 'ArrowUp') {
            player2.velocityY = -10;
        }
        if (e.key == 'ArrowDown') {
            player2.velocityY = 10;
        }
    }
}

function stopPlayer(e) {
    if (gameMod == 1 || gameMod == 2) {
        if (e.key == 'w') {
            player1.velocityY = 0;
        }
        if (e.key == 's') {
            player1.velocityY = 0;
        }
    }
    if (gameMod == 2) {
        if (e.key == 'ArrowUp') {
            player2.velocityY = 0;
        }
        if (e.key == 'ArrowDown') {
            player2.velocityY = 0;
        }
    }
}

function makeBot1Prediction() {
    let ballcpy_xPos = ball.xPos;
    let ballcpy_yPos = ball.yPos;
    let ballcpy_height = ball.height;
    let ballcpy_velocityX = ball.velocityX;
    let ballcpy_velocityY = ball.velocityY;
    let yDistance = 0;

    if (ballcpy_velocityY < 0)
        yDistance = 0;
    else
        yDistance = board_height;

    while (ballcpy_xPos + ballcpy_velocityX - 11 > 0) {
        ballcpy_xPos += ballcpy_velocityX;
        if (yDistance == 0) {
            if (ballcpy_yPos + ballcpy_velocityY > yDistance) {
                ballcpy_yPos += ballcpy_velocityY;
            }
            else {
                ballcpy_velocityY *= -1;
                ballcpy_yPos += ballcpy_velocityY;
            }
        }
        else {
            if (ballcpy_yPos + ballcpy_velocityY + ballcpy_height < yDistance) {
                ballcpy_yPos += ballcpy_velocityY;
            }
            else {
                ballcpy_velocityY *= -1;
                ballcpy_yPos += ballcpy_velocityY;
            }
        }

    }
    let res = ballcpy_xPos / (ballcpy_velocityX * -1);
    player1.prediction = ballcpy_yPos + ballcpy_height / 2 + ballcpy_velocityY * res;
    //console.log(player2.prediction);
}

function makeBot2Prediction() {
    let ballcpy_xPos = ball.xPos;
    let ballcpy_yPos = ball.yPos;
    let ballcpy_height = ball.height;
    let ballcpy_width = ball.width;
    let ballcpy_velocityX = ball.velocityX;
    let ballcpy_velocityY = ball.velocityY;
    let yDistance = 0;

    if (ballcpy_velocityY < 0)
        yDistance = 0;
    else
        yDistance = board_height;

    while (ballcpy_xPos + ballcpy_velocityX + ballcpy_width + 11 < board_width) {
        ballcpy_xPos += ballcpy_velocityX;
        if (yDistance == 0) {
            if (ballcpy_yPos + ballcpy_velocityY > yDistance) {
                ballcpy_yPos += ballcpy_velocityY;
            }
            else {
                ballcpy_velocityY *= -1;
                ballcpy_yPos += ballcpy_velocityY;
                if (ballcpy_velocityY < 0)
                    yDistance = 0;
                else
                    yDistance = board_height;
            }
        }
        else {
            if (ballcpy_yPos + ballcpy_velocityY + ballcpy_height < yDistance) {
                ballcpy_yPos += ballcpy_velocityY;
            }
            else {
                ballcpy_velocityY *= -1;
                ballcpy_yPos += ballcpy_velocityY;
                if (ballcpy_velocityY < 0)
                    yDistance = 0;
                else
                    yDistance = board_height;
            }
        }

    }
    let res = (board_width - ballcpy_xPos) / ballcpy_velocityX;
    player2.prediction = ballcpy_yPos + ballcpy_height / 2 + ballcpy_velocityY * res;
}

function play() {
    var audio = new Audio('utils/1.mp3');
    audio.play();
}
// function play2() {
//     var audio = new Audio('3.mp3');
//     audio.play();
// }