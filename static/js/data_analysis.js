document.addEventListener("DOMContentLoaded", function () {
    const sshStatus = document.getElementById('ssh-status');
    const modelSelect = document.getElementById("modelSelect");
    

    // 建立 WebSocket
    const socket = new WebSocket("ws://" + window.location.host + "/ws/CMD/");
    socket.onopen = function () {
        sshStatus.innerHTML = `<span class="text-success fw-bold">🟢 伺服器 已連線</span>`;
    };

    // 載入模型清單
    loadModelList();

    // 切換模型時
    modelSelect.addEventListener("change", function () {
        const modelName = this.value;
        if (modelName) loadModelImages(modelName);
    });
});

// 載入模型清單
function loadModelList() {
    fetch("/api/list_model_names/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({})
    })
    .then(res => res.json())
    .then(data => {
        const select = document.getElementById("modelSelect");
        select.innerHTML = "";

        if (data.models && data.models.length > 0) {
            data.models.forEach(name => {
                const option = document.createElement("option");
                option.value = name;
                option.textContent = name;
                select.appendChild(option);
            });
            // 預設載入第一個
            select.value = data.models[0];
            loadModelImages(data.models[0]);
        } else {
            select.innerHTML = `<option disabled>⚠️ 找不到模型檔案</option>`;
        }
    })
    .catch(err => {
        console.error("讀取模型清單失敗", err);
        document.getElementById("modelSelect").innerHTML = `<option disabled>🚫 載入失敗</option>`;
    });
}

// 載入圖片
function loadModelImages(modelName) {
    fetch("/api/get_model_images/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ model_name: modelName })
    })
    .then(res => res.json())
    .then(data => {
        if (data.images) {
            for (const [key, url] of Object.entries(data.images)) {
                const imgId = "img-" + key;
                const errId = "err-" + imgId;
                const img = document.getElementById(imgId);
                const err = document.getElementById(errId);

                if (url) {
                    img.src = url + `?t=${Date.now()}`;
                    img.style.display = "block";
                    if (err) err.classList.add("d-none");
                } else {
                    img.style.display = "none";
                    if (err) err.classList.remove("d-none");
                }
            }
        }
    })
    .catch(err => console.error("載入圖片失敗", err));
}

// 下載模型
function download() {
    const modelSelect = document.getElementById("modelSelect");
    const modelName = modelSelect.value;
    if (!modelName) {
        alert("請選擇模型名稱！");
        return;
    }

    fetch("/api/download_model/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ model_name: modelName })
    })
    .then(res => {
        if (!res.ok) throw new Error("下載失敗: " + res.statusText);
        return res.blob();
    })
    .then(blob => {
        const link = document.createElement("a");
        link.href = URL.createObjectURL(blob);
        link.download = `${modelName}.h5`;
        link.click();
        URL.revokeObjectURL(link.href);
    })
    .catch(err => console.error("下載失敗", err));
}