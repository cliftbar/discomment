const host = "{{ host }}"
const port = "{{ port }}"
const ws = new WebSocket("ws://" + host + ":" + port + "/ws");

ws.addEventListener("message", function (event) {
    let d = JSON.parse(event.data);
    for (let i = 0; i < d.length; i++) {
        let m = d[i]
        const li = document.createElement("li");
        li.appendChild(document.createTextNode(JSON.stringify(m)));
        document.getElementById("messages").prepend(li);
    }
});

function send(event) {
    const message = (new FormData(event.target)).get("message");
    if (message) {
      ws.send(message);
    }
    event.target.reset();
    return false;
}

function postComment() {
    let msg = document.getElementById("message").value
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