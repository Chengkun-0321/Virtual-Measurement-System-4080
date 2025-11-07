document.addEventListener("DOMContentLoaded", function() {
    const runTestButton = document.getElementById('run-test');
    const sshStatus = document.getElementById('ssh-status');
    const outputArea = document.getElementById('output');
    const confusionMatrixImg = document.getElementById('confusion-matrix');
    const groundTruthImg = document.getElementById('ground-truth');
    const checkpointSelect = document.getElementById("checkpoint-select");
    const socket = new WebSocket("ws://" + window.location.host + "/ws/TEST/");

    socket.onopen = function() {
        sshStatus.innerHTML = `<span class="text-success fw-bold">🟢 伺服器 已連線</span>`;
    };

    // 載入可用的 checkpoints
    fetch("/api/test_list_checkpoints/", {
        method: "POST"
    })
    .then(res => res.json())
    .then(data => {
        checkpointSelect.innerHTML = "";
        if (data.checkpoints.length > 0) {
            data.checkpoints.forEach(ckpt => {
                let option = document.createElement("option");
                option.value = ckpt;
                option.textContent = ckpt;
                checkpointSelect.appendChild(option);
            });
        } else {
            let option = document.createElement("option");
            option.disabled = true;
            option.textContent = "⚠️ 沒有找到權重檔";
            checkpointSelect.appendChild(option);
        }
    })
    .catch(err => {
        console.error("載入 checkpoints 失敗:", err);
        checkpointSelect.innerHTML = "<option disabled>載入失敗</option>";
    });


    socket.onmessage = function(event) {
        if (outputArea) {
            outputArea.value += event.data + "\n";
        }

        if (event.data.includes("finsh test!")) {
            runTestButton.disabled = false;
            runTestButton.innerHTML = '▶️ 執行模型測試';

            const checkpointPath = document.querySelector('select[name="checkpoint_path"]').value;
            fetch("/api/post_test_images/", {
                method: "POST",
                headers: { "Content-Type": "application/json", "X-CSRFToken": getCSRFToken() },
                body: JSON.stringify({ model_name: checkpointPath })
            })
            .then(res => res.json())
            .then(data => {
                confusionMatrixImg.src = data.images.mape + "?t=" + Date.now();
                groundTruthImg.src = data.images.ground_truth + "?t=" + Date.now();
                document.getElementById('confusion-hint').style.display = 'none';
                document.getElementById('groundtruth-hint').style.display = 'none';
            });
        }
    };

    runTestButton.addEventListener('click', async function() {
        runTestButton.disabled = true;
        runTestButton.innerHTML = '<span class="spinner-border spinner-border-sm"></span> 執行中...';

        const formData = new FormData(document.querySelector('#test-form'));
        const payload = {
            model: formData.get('model'),
            dataset: formData.get('dataset'),
            checkpoint_path: formData.get('checkpoint_path'),
            mean: formData.get('mean'),
            boundary_upper: formData.get('boundary_upper'),
            boundary_lower: formData.get('boundary_lower')
        };

        // 先打 REST API 確認參數
        let resp = await fetch("/api/test/", {
            method: "POST",
            headers: { "Content-Type": "application/json", "X-CSRFToken": "{{ csrf_token }}" },
            body: JSON.stringify(payload)
        });
        let result = await resp.json();
        console.log("API Response:", result);

        // 如果成功，透過 WebSocket 發送執行指令
        if (result.status === "submitted") {
            socket.send(JSON.stringify({ action: "run-test", ...payload }));
        } else {
            alert(result.message);
            runTestButton.disabled = false;
            runTestButton.innerHTML = '▶️ 執行模型測試';
        }
    });

    function getCSRFToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]').value;
    }
});