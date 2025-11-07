document.getElementById("loginForm").addEventListener("submit", function (e) {
    e.preventDefault();

    let formData = new FormData(this);
    formData.append("account", formData.get("username"));

    fetch("/api/login/", {
        method: "POST",
        body: formData,
    })
    .then(res => {
        console.log("🔥 API 回應狀態碼：", res.status);
        console.log("🔥 API Content-Type：", res.headers.get("content-type"));
        return res.json();
    })
    .then(data => {
        const messageBox = document.getElementById("messageBox");

        // 顯示訊息
        messageBox.innerHTML = `
            <div id="login-message" class="alert alert-${data.status === "success" ? "success" : "danger"} text-center">
                ${data.message}
            </div>
        `;

        if (data.status === "success") {
            // 儲存新的 CSRF token 到 localStorage
            localStorage.setItem("csrftoken", data.csrfToken);

            setTimeout(() => {
                window.location.href = "/home/";
            }, 1000);
        } else {
            setTimeout(() => {
                const msg = document.getElementById("login-message");
                if (msg) msg.remove();
            }, 1500);
        }
    })
    .catch(error => console.error("JSON 解析錯誤", error));
});