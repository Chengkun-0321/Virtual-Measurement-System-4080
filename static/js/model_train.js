document.addEventListener("DOMContentLoaded", function() {
    const runTrainButton = document.getElementById('run-train');
    const sshStatus = document.getElementById('ssh-status');
    const socket = new WebSocket("ws://" + window.location.host + "/ws/TRAIN/");

    // 伺服器連線狀態
    socket.onopen = function() {
        sshStatus.innerHTML = `<span class="text-success fw-bold">🟢 伺服器 已連線</span>`;
    };

    // 訓練曲線圖即時變化
    // Chart 初始化
    const ctx1 = document.getElementById('LossChart').getContext('2d');
    const LossChart = new Chart(ctx1, { type: 'line', data: { labels: [], datasets: [
        { label: 'train', data: [], borderColor: 'blue', fill: false},
        { label: 'test', data: [], borderColor: 'orange', fill: false}
    ]}, options: { responsive: true, animation: false, spanGaps: true }});

    const ctx2 = document.getElementById('AccChart').getContext('2d');
    const AccChart = new Chart(ctx2, { type: 'line', data: { labels: [], datasets: [
        { label: 'train', data: [], borderColor: 'blue', fill: false},
        { label: 'test', data: [], borderColor: 'orange', fill: false}
    ]}, options: { responsive: true, animation: false, spanGaps: true }});

    socket.onmessage = function(event) {
        const data = event.data;
        console.log("WS Message:", data);

        // 更新訓練曲線
        window.allEpochs = window.allEpochs || [];
        window.allLoss = window.allLoss || [];
        window.allValLoss = window.allValLoss || [];
        window.allMae = window.allMae || [];
        window.allValMae = window.allValMae || [];
        
        let epochMatch = data.match(/Epoch\s+(\d+)\/\d+/);
        if (epochMatch) {
            const epoch = parseInt(epochMatch[1]);
            window.allEpochs.push(epoch);
        }

        let lossMatch = data.match(/loss:\s*([\d.]+)/);
        if (lossMatch) {
            const loss = parseFloat(lossMatch[1]);
            if (window.allLoss.length < window.allEpochs.length) {
                window.allLoss.push(loss);
            } else {
                window.allLoss[window.allEpochs.length - 1] = loss;
            }
            LossChart.data.datasets[0].data = window.allLoss.slice(-50);
        }

        let vallossMatch = data.match(/val_loss:\s*([\d.]+)/);
        if (vallossMatch) {
            const val_loss = parseFloat(vallossMatch[1]);
            if (window.allValLoss.length < window.allEpochs.length) {
                window.allValLoss.push(val_loss);
            } else {
                window.allValLoss[window.allEpochs.length - 1] = val_loss;
            }
            LossChart.data.datasets[1].data = window.allValLoss.slice(-50);
        }

        let accMatch = data.match(/mae:\s*([\d.]+)/);
        if (accMatch) {
            const mae = parseFloat(accMatch[1]);
            const acc = (100 - mae);
            if (window.allMae.length < window.allEpochs.length) {
                window.allMae.push(acc);
            } else {
                window.allMae[window.allEpochs.length - 1] = acc;
            }
            AccChart.data.datasets[0].data = window.allMae.slice(-50);
        }

        let valaccMatch = data.match(/val_mae:\s*([\d.]+)/);
        if (valaccMatch) {
            const val_mae = parseFloat(valaccMatch[1]);
            const val_acc = (100 - val_mae);
            if (window.allValMae.length < window.allEpochs.length) {
                window.allValMae.push(val_acc);
            } else {
                window.allValMae[window.allEpochs.length - 1] = val_acc;
            }
            AccChart.data.datasets[1].data = window.allValMae.slice(-50);
        }

        LossChart.data.labels = window.allEpochs.slice(-50);
        LossChart.update();
        AccChart.data.labels = window.allEpochs.slice(-50);
        AccChart.update();

        // 收到 finish 關鍵字 → 解鎖按鈕
        if (data.includes("__FINISHED__")) {       
            runTrainButton.disabled = false;
            runTrainButton.innerHTML = '▶️ 執行模型訓練';
        }
    };

    // 點擊訓練按鈕功能
    runTrainButton.addEventListener('click', async function() {
        runTrainButton.disabled = true;
        runTrainButton.innerHTML = '<span class="spinner-border spinner-border-sm"></span> 執行中...';

        const form = document.querySelector('#train-form');
        const formData = new FormData(form);
        
        const payload = {
            model: formData.get('model'),
            dataset: formData.get('dataset'),
            epochs: formData.get('epochs'),
            batch_size: formData.get('batch_size'),
            learning_rate: formData.get('learning_rate'),
            validation_freq: formData.get('validation_freq')
        };

        // 點擊訓練 打 /api/train
        try {
            let resp = await fetch("/api/train/", {
                method: "POST",
                headers: { "Content-Type": "application/json", "X-CSRFToken": "{{ csrf_token }}" },
                body: JSON.stringify(payload)
            });
            let result = await resp.json();
            
            console.log("API Response:", result);
            console.log("判斷結果:", result.status);

            if (result.status === "submitted") {
                const taskId = result.task_id;
                //checkTaskStatus(taskId);
            } else {
                alert(result.message);
                runTrainButton.disabled = false;
                runTrainButton.innerHTML = '▶️ 執行模型訓練';
            }

        } catch (err) {
            console.error("API Error:", err);
            alert("❌ API 請求失敗，請檢查伺服器");
            runTrainButton.disabled = false;
            runTrainButton.innerHTML = '▶️ 執行模型訓練';
        }
    });

    // 定期檢查任務狀態(目前第127註解，所以為用)
    async function checkTaskStatus(taskId) {
        let timer = setInterval(async () => {
            let resp = await fetch(`/task/${taskId}/`);
            let result = await resp.json();
            console.log("Task Status:", result);

            if (result.status === "SUCCESS") {
                clearInterval(timer);
                runTrainButton.disabled = false;
                runTrainButton.innerHTML = '▶️ 執行模型訓練';
                alert("✅ 訓練完成！");
            } else if (result.status === "FAILURE") {
                clearInterval(timer);
                runTrainButton.disabled = false;
                runTrainButton.innerHTML = '▶️ 執行模型訓練';
                alert("❌ 訓練失敗！");
            }
        }, 2000);
    }
});