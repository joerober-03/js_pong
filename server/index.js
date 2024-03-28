const WebSocket = require("ws");

const wss = new WebSocket.Server({port: 443});

let clients = {
    id : 1,
    num : 1
}

let ready = {
    id : 2,
    isready : 0
}

var client_count = 0;

wss.on("connection", ws => {
    console.log("new client arrived");
    ws.send(JSON.stringify(clients));
    clients.num++;
    if (clients.num > 2)
        clients.num = 1;

    ws.on("message", client_message => {
        let array = JSON.parse(client_message);
        //console.log(array);
        if (array.id == 3)
        {
            client_count++;
        }
        if (array.id == 4)
        {
            if (client_count > 0)
                client_count--;
            console.log("client left");
        }
        if (client_count < 2)
        {
            ready.isready = 0;
            wss.clients.forEach(function each(client) {
                client.send(JSON.stringify(ready));
            });
        }
        if (client_count == 2)
        {
            ready.isready = 1;
            wss.clients.forEach(function each(client) {
                client.send(JSON.stringify(ready));
            });
        }
        wss.clients.forEach(function each(client) {
            client.send(JSON.stringify(array));
        });
        console.log(client_count);
    });
    ws.on("close", () => {
        client_count--;
        console.log("client left");
    })
});