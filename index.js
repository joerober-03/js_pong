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
let ball_velocity = 9;

let ball = {
    width : ball_width,
    height : ball_height,
    xPos : (board_width / 2) - (ball_width / 2),
    yPos : (board_height / 2) - (ball_height / 2),
    velocityY : 0,
    velocityX : 0,
    velocityXTmp : 0,
    velocityYTmp : 0,
    pause : 0
}

let player1 = {
    xPos : 10, 
    yPos : board_height / 2,
    width : player_width,
    height : player_height,
    velocityY : playerVelocity,
    score : 0
}

let player2 = {
    xPos : board_width - player_width - 10, 
    yPos : board_height / 2,
    width : player_width,
    height : player_height,
    velocityY : playerVelocity,
    score : 0
}

window.onload = function() {
    let board = document.getElementById("board");
    board.width = board_width;
    board.height = board_height;
    context = board.getContext("2d");
    context.fillStyle = "white";

    //player 1
    context.fillRect(player1.xPos, player1.yPos - player_height / 2, player1.width, player1.height);

    //player 2
    context.fillRect(player2.xPos, player2.yPos - player_height / 2, player2.width, player2.height);

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
    if (ran == 0)
        tmp *= -1;
    setTimeout(() => { ball.velocityY = Math.floor(Math.random() * 11) - 5; }, 500);
    setTimeout(() => { ball.velocityX = tmp; }, 500);

    window.requestAnimationFrame(gameLoop);
    document.addEventListener("keydown", movePlayer);
    document.addEventListener("keyup", stopPlayer);
}

function gameLoop() {
    window.requestAnimationFrame(gameLoop);

    context.clearRect(0, 0, board.width, board.height);
    //player 1
    if (player1.yPos + player1.velocityY - player1.height / 2 > 0 && player1.yPos + player1.velocityY + player1.height / 2 < board_height)
        player1.yPos += player1.velocityY;
    context.fillRect(player1.xPos, player1.yPos - player_height / 2, player1.width, player1.height);

    //player 2
    context.fillRect(player2.xPos, player2.yPos - player_height / 2, player2.width, player2.height);
    if (player2.yPos + player2.velocityY - player1.height / 2 > 0 && player2.yPos + player2.velocityY + player2.height / 2 < board_height)
        player2.yPos += player2.velocityY;

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
    if (!(ball.yPos + ball.velocityY + ball.height / 2 > 0 && ball.yPos + ball.velocityY + ball.height / 2 < board_height))
    {
        ball.velocityY *= -1;
    }
    if (ball.xPos + ball.velocityX + ball.width >= board_width - 11)
    {
        if (ball.yPos + ball.velocityY + ball.height > player2.yPos - 5 - player2.height / 2 && ball.yPos + ball.velocityY + ball.height <= player2.yPos + 5 + player2.height - player2.height / 2)
        {
            ball.velocityY = ((ball.yPos) - (player2.yPos)) / 5;
            ball.velocityX *= -1;
            if (ball.velocityX < 0)
                ball.velocityX -= 0.2;
            else
                ball.velocityX += 0.2;
        }
    }
    if (ball.xPos + ball.velocityX <= 11)
    {
        if (ball.yPos + ball.velocityY + ball.height > player1.yPos - 5 - player1.height / 2 && ball.yPos + ball.velocityY + ball.height <= player1.yPos + 5 + player1.height - player1.height / 2)
        {
            ball.velocityY = ((ball.yPos) - (player1.yPos))/ 5;
            ball.velocityX *= -1;
            if (ball.velocityX < 0)
                ball.velocityX -= 0.2;
            else
                ball.velocityX += 0.2;
        }
    }
    if (!(ball.xPos + ball.velocityX + ball.width / 2 > 0 && ball.xPos + ball.velocityX + ball.width / 2 < board_width))
    {
        if (!(ball.xPos + ball.velocityX + ball.width / 2 > 0))
            player2.score++;
        else
            player1.score++;
        ball.xPos = (board_width / 2) - (ball_width / 2);
        ball.yPos = (board_height / 2) - (ball_height / 2);
        let ran = Math.floor(Math.random() * 2);
        ball.velocityX = ball_velocity;
        if (ran == 0)
            ball.velocityX *= -1;
        ball.velocityY = Math.floor(Math.random() * 11) - 5;
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
        player1.velocityY = -11; 
    }
    if (e.key == 's')
    {
        player1.velocityY = 11;
    }
    if (e.key == 'ArrowUp')
    {
        player2.velocityY = -11; 
    }
    if (e.key == 'ArrowDown')
    {
        player2.velocityY = 11;
    }
    // if (e.key == 'q')
    // {
    //     ball.velocityX -= 2;
    //     ball.velocityY -= 2;
    // }
    // if (e.key == 'e')
    // {
    //     ball.velocityX += 2;
    //     ball.velocityY += 2;
    // }

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