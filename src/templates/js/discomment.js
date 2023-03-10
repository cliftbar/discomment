const host = "{{ host }}"
const port = "{{ port }}"
const apikey = "{{ apikey }}"
const channelId = "{{ channelId }}"
const baseUrl = host + ":" + port
// const ws = new WebSocket("ws://" + host + ":" + port + "/ws/comments?auth=" + apikey + "&channelId=" + channelId.toString());
//
// ws.addEventListener("message", function (event) {
//     let d = JSON.parse(event.data);
//     for (let i = 0; i < d.length; i++) {
//         let m = d[i]
//         const li = document.createElement("li");
//         li.appendChild(document.createTextNode(JSON.stringify(m)));
//         document.getElementById("ul_messages").prepend(li);
//     }
// });

let source = new EventSource("http://" + baseUrl + "/sse/comments?auth=" + apikey + "&channelId=" + channelId.toString());
source.onmessage = function(event) {
    console.log('Incoming data:' + event.data);

    let d = JSON.parse(event.data);
    for (let i = 0; i < d.length; i++) {
        let m = d[i]
        const li = document.createElement("li");
        li.appendChild(document.createTextNode(JSON.stringify(m)));
        document.getElementById("ul_messages").prepend(li);
    }
};

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
    let author = document.getElementById("inpt_author").value
    let url = "http://" + host + ":" + port + "/api/msg"

    let body = {"message": msg, "channelId": channelId}

    if (author !== "") {
        body["author"] = author
    }

    fetch(url, {
        method: "POST",
        body: JSON.stringify(body),
        headers: {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + apikey
        }
    }).then(res => {
        console.log(res)
        if (res.status === 420) {
            alert("You've been auto-moderated! Clean up the message and try again, and sorry for any false positives.")
        }
    })
}

function getComments() {
    let url = "http://" + host + ":" + port + "/api/msg?channelId=" + channelId.toString()

    fetch(url, {
        method: "GET",
        headers: {
            "Authorization": "Bearer " + apikey
        }
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