const host = "{{ host }}"
const port = "{{ port }}"
const ws = new WebSocket("ws://" + host + ":" + port + "/ws");

ws.addEventListener("message", function (event) {
    let d = JSON.parse(event.data);
    for (let i = 0; i < d.length; i++) {
        let m = d[i]
        const li = document.createElement("li");
        li.appendChild(document.createTextNode(JSON.stringify(m)));
        document.getElementById("ul_messages").prepend(li);
    }
});

function send(event) {
    const message = (new FormData(event.target)).get("inpt_message");
    if (message) {
        ws.send(message);
    }
    event.target.reset();
    return false;
}

function postComment() {
    let msg = document.getElementById("inpt_message").value
    let url = "http://" + host + ":" + port + "/api/msg"

    fetch(url, {
        method: "POST",
        body: JSON.stringify({"message": msg}),
        headers: {
            "Content-Type": "application/json"
        }
    }).then(res => {
        console.log(res)
    })
}

function getComments() {
    let url = "http://" + host + ":" + port + "/api/msg"

    fetch(url, {
        method: "GET",
    }).then(r => r.json()).then(resJson => {
        console.log(resJson)
        let msgList = document.getElementById("ul_messages")
        for (const msg of resJson) {
            let li = document.createElement("li")
            li.textContent = JSON.stringify(msg)
            msgList.appendChild(li)
        }
    })
}