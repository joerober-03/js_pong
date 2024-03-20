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
    width : ball_width,
    height : ball_height,
    xPos : (board_width / 2) - (ball_width / 2),
    yPos : (board_height / 2) - (ball_height / 2),
    velocityY : 0,
    velocityX : 0,
    velocityXTmp : 0,
    velocityYTmp : 0
}

let player1 = {
    xPos : 10, 
    yPos : board_height / 2 - player_height / 2,
    width : player_width,
    height : player_height,
    velocityY : playerVelocity,
    score : 0,
    prediction : -1
}

let player2 = {
    xPos : board_width - player_width - 10, 
    yPos : board_height / 2 - player_height / 2,
    width : player_width,
    height : player_height,
    velocityY : playerVelocity,
    score : 0,
    prediction : -1
}

window.onload = function() {
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
    context.fillText(player1.score, 10, 50);

    context.fillText(player2.score, 200, 50);

    //ball
    context.fillRect(ball.xPos, ball.yPos, ball.width, ball.height);

    let ran = Math.floor(Math.random() * 2);
    let tmp = ball_velocity;
    let tmp2 = Math.floor(Math.random() * 11) - 5;
    ball.velocityY = tmp2;
    if (ran == 0)
    {
        tmp *= -1;
    }
    ball.velocityX = tmp;
    if (ran == 1)
        makeBot2Prediction();
    // else
    //     makeBot1Prediction();
    ball.velocityX = 0;
    ball.velocityY = 0;
    setTimeout(() => { ball.velocityY = tmp2; }, 500);
    setTimeout(() => { ball.velocityX = tmp; }, 500);

    window.requestAnimationFrame(gameLoop);
    document.addEventListener("keydown", movePlayer);
    document.addEventListener("keyup", stopPlayer);
}

function gameLoop() {
    window.requestAnimationFrame(gameLoop);

    context.clearRect(0, 0, board.width, board.height);
    //bot1 movement
    // if (player1.prediction >= player1.yPos && player1.prediction <= player1.yPos + player1.height || player1.prediction == -1)
    //     player1.velocityY = 0;
    // else
    // {
    //     if (player1.yPos + player1.height < player1.prediction)
    //         player1.velocityY = 10;
    //     if (player1.yPos > player1.prediction)
    //         player1.velocityY = -10;
    // }
    
    //player 1
    if (player1.yPos + player1.velocityY > 0 && player1.yPos + player1.velocityY + player1.height < board_height)
        player1.yPos += player1.velocityY;
    else if (!(player1.yPos + player1.velocityY > 0))
        player1.yPos = 2;
    else
        player1.yPos = board_height - player1.height - 2;
    context.fillRect(player1.xPos, player1.yPos, player1.width, player1.height);

    //bot2 movement

    if (player2.prediction >= player2.yPos && player2.prediction <= player2.yPos + player2.height || player2.prediction == -1)
        player2.velocityY = 0;
    else
    {
        if (player2.yPos + player2.height < player2.prediction)
            player2.velocityY = 10;
        if (player2.yPos > player2.prediction)
            player2.velocityY = -10;
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

    //score
    context.fillText(player1.score, 100, 50);

    context.fillText(player2.score, board_width - 130, 50);

    //ball
    changeBallVelocity();
    ball.xPos += ball.velocityX;
    ball.yPos += ball.velocityY;
    context.fillRect(ball.xPos, ball.yPos, ball.width, ball.height);
}

function fill_middle_lines()
{
    for (let i = 0; i < board_height; i += 4.2)
    {
        context.fillStyle = "white";
        context.fillRect(board_width / 2 - 5, i, 10, 30);
        i += 60;
    }
}

function changeBallVelocity()
{
    if (!(ball.yPos + ball.velocityY > 0 && ball.yPos + ball.velocityY + ball.height < board_height))
    {
        ball.velocityY *= -1;
    }
    if (ball.xPos + ball.velocityX + ball.width >= board_width - 11)
    {
        if (ball.yPos + ball.velocityY + ball.height + 2 >= player2.yPos && ball.yPos + ball.velocityY - 2 <= player2.yPos + player2.height)
        {
            ball.velocityY = ((ball.yPos + ball.height / 2) - (player2.yPos + player2.height / 2)) / 7;
            ball.velocityX *= -1;
            if (ball.velocityX < 0)
                ball.velocityX -= 0.5;
            else
                ball.velocityX += 0.5;
            //makeBot1Prediction();
            play();
        }
    }
    if (ball.xPos + ball.velocityX <= 11)
    {
        if (ball.yPos + ball.velocityY + ball.height + 2 >= player1.yPos && ball.yPos + ball.velocityY - 2 <= player1.yPos + player1.height)
        {
            ball.velocityY = ((ball.yPos + ball.height / 2) - (player1.yPos + player1.height / 2)) / 7;
            ball.velocityX *= -1;
            if (ball.velocityX < 0)
                ball.velocityX -= 0.5;
            else
                ball.velocityX += 0.5;
            makeBot2Prediction();
            play();
        }
    }
    if (!(ball.xPos + ball.velocityX > 0 && ball.xPos + ball.velocityX + ball.width < board_width))
    {
        if (!(ball.xPos + ball.velocityX > 0))
            player2.score++;
        else
            player1.score++;
        ball.xPos = (board_width / 2) - (ball_width / 2);
        ball.yPos = (board_height / 2) - (ball_height / 2);
        let ran = Math.floor(Math.random() * 2);
        ball.velocityX = ball_velocity;
        ball.velocityY = Math.floor(Math.random() * 11) - 5;
        if (ran == 0)
            ball.velocityX *= -1;
        if (ball.velocityX > 0)
            makeBot2Prediction();
        //else
        //    makeBot1Prediction();
        ball.velocityXTmp = ball.velocityX;
        ball.velocityYTmp = ball.velocityY;
        ball.velocityX = 0;
        ball.velocityY = 0;
        setTimeout(() => { ball.velocityY = ball.velocityYTmp; }, 500);
        setTimeout(() => { ball.velocityX = ball.velocityXTmp; }, 500);
    }
}

function movePlayer(e)
{

    if (e.key == 'w')
    {
        player1.velocityY = -10; 
    }
    if (e.key == 's')
    {
        player1.velocityY = 10;
    }
    if (e.key == 'ArrowUp')
    {
        player2.velocityY = -10; 
    }
    if (e.key == 'ArrowDown')
    {
        player2.velocityY = 10;
    }
}

function stopPlayer(e)
{
    if (e.key == 'w')
    {
        player1.velocityY = 0;
    }
    if (e.key == 's')
    {
        player1.velocityY = 0;
    }
    if (e.key == 'ArrowUp')
    {
        player2.velocityY = 0;
    }
    if (e.key == 'ArrowDown')
    {
        player2.velocityY = 0;
    }
}

function makeBot1Prediction()
{
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

    while (ballcpy_xPos + ballcpy_velocityX - 11 > 0)
    {
        ballcpy_xPos += ballcpy_velocityX;
        if (yDistance == 0)
        {
            if (ballcpy_yPos + ballcpy_velocityY > yDistance)
            {
                ballcpy_yPos += ballcpy_velocityY;
            }
            else
            {
                ballcpy_velocityY *= -1;
                ballcpy_yPos += ballcpy_velocityY;
            }
        }
        else
        {
            if (ballcpy_yPos + ballcpy_velocityY + ballcpy_height < yDistance)
            {
                ballcpy_yPos += ballcpy_velocityY;
            }
            else
            {
                ballcpy_velocityY *= -1;
                ballcpy_yPos += ballcpy_velocityY;
            }
        }

    }
    let res = ballcpy_xPos / (ballcpy_velocityX * -1);
    player1.prediction = ballcpy_yPos + ballcpy_height / 2 + ballcpy_velocityY * res;
    console.log(player2.prediction);
}

function makeBot2Prediction()
{
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

    while (ballcpy_xPos + ballcpy_velocityX + ballcpy_width + 11 < board_width)
    {
        ballcpy_xPos += ballcpy_velocityX;
        if (yDistance == 0)
        {
            if (ballcpy_yPos + ballcpy_velocityY > yDistance)
            {
                ballcpy_yPos += ballcpy_velocityY;
            }
            else
            {
                ballcpy_velocityY *= -1;
                ballcpy_yPos += ballcpy_velocityY;
                if (ballcpy_velocityY < 0)
                    yDistance = 0;
                else
                    yDistance = board_height;
            }
        }
        else
        {
            if (ballcpy_yPos + ballcpy_velocityY + ballcpy_height < yDistance)
            {
                ballcpy_yPos += ballcpy_velocityY;
            }
            else
            {
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
    var audio = new Audio('1.mp3');
    audio.play();
}
// function play2() {
//     var audio = new Audio('3.mp3');
//     audio.play();
// }