document.addEventListener("DOMContentLoaded", function () {
    const sshStatus = document.getElementById('ssh-status');
    const socket = new WebSocket("ws://" + window.location.host + "/ws/DEPLOY/");

    socket.onopen = function () {
        sshStatus.innerHTML = `<span class="text-success fw-bold">🟢 伺服器 已連線</span>`;
    };

    // 取得模型清單
    fetch('/api/deploy_list_checkpoints/')
    .then(res => res.json())
    .then(data => {
        const select = document.getElementById('model-select');
        data.models.forEach(model => {
            const opt = document.createElement('option');
            opt.value = model;
            opt.textContent = model;
            select.appendChild(opt);
        });
    });

    // 上傳 npy
    document.getElementById('upload-form').addEventListener('submit', function (e) {
        e.preventDefault();
        const formData = new FormData(this);

        fetch('/api/import_npy/', {
            method: 'POST',
            body: formData
        })
        .then(res => res.json())
        .then(data => {
            if (data.columns && data.rows) {
                const table = document.getElementById('data-table');
                const thead = table.querySelector('thead');
                const tbody = table.querySelector('tbody');
                thead.innerHTML = '';
                tbody.innerHTML = '';

                // 標題列
                const headRow = document.createElement('tr');
                headRow.innerHTML = `<th><input type="checkbox" id="select-all"></th>` + data.columns.map(col => `<th>${col}</th>`).join('');
                thead.appendChild(headRow);

                // 資料列
                data.rows.forEach((row, i) => {
                    const rowHtml = `<td><input type="checkbox" class="row-select" value="${i}"></td>` +
                        row.map(val => `<td>${val}</td>`).join('');
                    const tr = document.createElement('tr');
                    tr.innerHTML = rowHtml;
                    tbody.appendChild(tr);
                });

                document.getElementById('data-table-container').classList.remove('d-none');
            }
        });
    });

    // 全選 / 取消全選
    document.addEventListener('change', function (e) {
        if (e.target && e.target.id === 'select-all') {
            document.querySelectorAll('.row-select').forEach(cb => cb.checked = e.target.checked);
        }
    });

    // 左右表格同步滾動
    const left = document.getElementById('data-table-container');
    const right = document.getElementById('prediction-table-container');
    left.addEventListener('scroll', () => { right.scrollTop = left.scrollTop; });
    right.addEventListener('scroll', () => { left.scrollTop = right.scrollTop; });

    // 預測
    document.getElementById('predict-btn').addEventListener('click', function () {
        const checkboxes = document.querySelectorAll('.row-select:checked');
        const selectedIndices = Array.from(checkboxes).map(cb => parseInt(cb.value));
        const modelName = document.getElementById('model-select').value;

        fetch('/api/predict/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ indices: selectedIndices, model: modelName })
        })
        .then(res => res.json())
        .then(data => {
            if (data.status === "submitted") {
                console.log("預測任務已提交，等待 WebSocket 推送結果...");
            } else {
                alert("預測失敗：" + (data.error || "未知錯誤"));
            }
        })
        .catch(err => {
            alert("預測請求失敗：" + err);
        });
    });

    socket.onmessage = function (event) {
        const logBox = document.getElementById('prediction-result');  // 用來顯示結果
        const msg = event.data;

        // 如果是預測結果
        if (msg.startsWith("結果:")) {
            const raw = msg.replace("結果: ", "").trim();
            const predictions = JSON.parse(raw.replace(/'/g, '"')); // 把字串轉成 Array
            console.log("收到預測結果:", predictions);

            // 顯示在右側表格
            const predictionContainer = document.getElementById('prediction-table-container');
            const predictionTableBody = document.querySelector('#prediction-table tbody');
            predictionTableBody.innerHTML = '';

            predictionContainer.classList.remove('d-none');

            predictions.forEach((value, i) => {
                const tr = document.createElement('tr');
                tr.innerHTML = `<td>${i + 1}</td><td>${value}</td>`;
                predictionTableBody.appendChild(tr);
            });

            logBox.innerHTML = `<strong>✅ 預測完成，共 ${predictions.length} 筆資料。</strong>`;
        } else {
            // 普通 log 訊息（例如 "載入模型..."、"開始預測..."）
            const logDiv = document.getElementById('deploy-log');
            logDiv.innerHTML += msg + "<br>";
        }
    };
});