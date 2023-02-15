const protocol = "{{ protocol }}";
const host = "{{ host }}";
const port = "{{ port }}";
const baseUrl = `${protocol}://${host}:${port}`;

let source;

function startCommentTest() {
    let testApiKey = document.getElementById("inpt_testApiKey").value;

    source = new EventSource(`${baseUrl}/sse/comments?auth${testApiKey}`);
    source.onmessage = function (event) {
        console.log('Incoming data:' + event.data);

        let d = JSON.parse(event.data);
        for (let i = 0; i < d.length; i++) {
            let m = d[i];
            const li = document.createElement("li");
            li.appendChild(document.createTextNode(JSON.stringify(m)));
            document.getElementById("ul_messages").prepend(li);
        }
    };

    getComments();
}


function postComment() {
    let testApiKey = document.getElementById("inpt_testApiKey").value;
    let testChannelId = document.getElementById("inpt_testChannelId").value;

    let msg = document.getElementById("inpt_message").value;
    let author = document.getElementById("inpt_author").value;
    let url = `${baseUrl}/api/msg`;

    let body = {"message": msg, "channelId": testChannelId};

    if (author !== "") {
        body["author"] = author;
    }

    fetch(url, {
        method: "POST", body: JSON.stringify(body), headers: {
            "Content-Type": "application/json", "Authorization": `Bearer ${testApiKey}`
        }
    }).then(res => {
        console.log(res);
        if (res.status === 420) {
            alert("You've been auto-moderated! Clean up the message and try again, and sorry for any false positives.");
        }
    });
}

function getComments() {
    let testApiKey = document.getElementById("inpt_testApiKey").value;
    let testChannelId = document.getElementById("inpt_testChannelId").value;

    let url = `${baseUrl}/api/msg?channelId=${testChannelId}`;

    fetch(url, {
        method: "GET", headers: {
            "Authorization": `Bearer ${testApiKey}`
        }
    }).then(r => r.json()).then(resJson => {
        console.log(resJson);
        let msgList = document.getElementById("ul_messages");
        for (const msg of resJson) {
            let li = document.createElement("li");
            li.textContent = JSON.stringify(msg);
            msgList.appendChild(li);
        }
    });
}

function postCreateNamespace() {
    let namespace = document.getElementById("tbx_namespace").value;

    let url = `${baseUrl}/api/auth/namespace`;

    let body = {
        "namespace": namespace,
    };

    fetch(url, {
        method: "POST", body: JSON.stringify(body), headers: {
            "Content-Type": "application/json"
        }
    }).then(r => {
        if (r.ok) {
            return r.json();
        } else {
            throw r;
        }
    }).then(data => {
        alert(`Namespace ${data["namespace"]} created.  Admin API Token: ${data['adminApiKey']}`);
    }).catch(errResp => {
        if (errResp.status === 409) {
            alert(`Namespace ${namespace} already exists!`);
        }
    });
}

function postCreateApiKey() {
    let namespace = document.getElementById("tbx_namespace").value;
    let apiKeyId = document.getElementById("tbx_apiKeyId").value;
    let channelId = document.getElementById("inpt_testChannelId").value;
    let allowedDomains = document.getElementById("tbx_allowedDomains").value.split(",");
    let allDomains = document.getElementById("chbx_allowAllDomains").checked;
    let doModeration = document.getElementById("chbx_doModeration").checked;
    let adminApiKey = document.getElementById("tbx_adminApikey").value;

    let url = `${baseUrl}/api/auth/apikey`;

    let body = {
        "namespace": namespace,
        "identifier": apiKeyId,
        "moderation": doModeration,
        "channelId": channelId,
        "scopes": ["admin", "account_read", "account_write", "ws_read"]
    };

    if (allDomains === true) {
        body["allowedHosts"] = ["*"];
    } else {
        body["allowedHosts"] = allowedDomains;
    }

    fetch(url, {
        method: "POST", body: JSON.stringify(body), headers: {
            "Content-Type": "application/json", "Authorization": `Bearer ${adminApiKey}`
        }
    }).then(r => {
        if (r.ok) {
            return r.json();
        } else {
            throw r;
        }
    }).then(data => {
        alert(`Here is your API Key: ${data["apikey"]}. It will only be displayed this one time.`);
    }).catch(errResp => {
        console.log(errResp.status);
    });
}
