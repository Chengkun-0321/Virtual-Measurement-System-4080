document.addEventListener("DOMContentLoaded", function() {
    const sshStatus = document.getElementById('ssh-status');
    const tableBody = document.querySelector("#weights-table tbody");

    // WebSocket 狀態
    const socket = new WebSocket("ws://" + window.location.host + "/ws/CMD/");
    socket.onopen = function() {
        sshStatus.innerHTML = `<span class="text-success fw-bold">🟢 伺服器 已連線</span>`;
    };

    // 篩選條件事件
    document.getElementById("filter-name").addEventListener("input", loadWeights);
    document.getElementById("sort-date").addEventListener("change", function() {
        document.getElementById("sort-acc").value = "none";
        loadWeights();
    });
    document.getElementById("sort-acc").addEventListener("change", function() {
        document.getElementById("sort-date").value = "none";
        loadWeights();
    });

    // 載入模型列表 (GET)
    async function loadWeights() {
        let url = "/api/list_checkpoint/";
        const params = [];
        const dateSort = document.getElementById("sort-date").value;
        const accSort = document.getElementById("sort-acc").value;

        if (dateSort && dateSort !== "none") {
            const [sort_by, order] = dateSort.split("_");
            params.push(`sort_by=${sort_by}`);
            params.push(`order=${order}`);
        }
        if (accSort && accSort !== "none") {
            const [sort_by, order] = accSort.split("_");
            params.push(`sort_by=${sort_by}`);
            params.push(`order=${order}`);
        }
        if (params.length > 0) url += "?" + params.join("&");

        try {
            const resp = await fetch(url);
            const data = await resp.json();

            const nameFilter = document.getElementById("filter-name").value.toLowerCase();
            const filtered = data.filter(file => !nameFilter || file.name.toLowerCase().includes(nameFilter));

            tableBody.innerHTML = "";
            if (filtered.length === 0) {
                tableBody.innerHTML = '<tr><td colspan="4" class="text-center text-muted">📂 沒有符合條件的模型檔案</td></tr>';
                return;
            }

            filtered.forEach(file => {
                const row = document.createElement("tr");
                row.innerHTML = `
                    <td>${file.name}.h5</td>
                    <td>${file.date}</td>
                    <td>${file.acc !== null ? parseFloat(file.acc).toFixed(2) : "-"} %</td>
                    <td>
                        <button class="btn btn-sm btn-outline-primary rename-btn" data-old="${file.name}">✏️ 修改名稱</button>
                        <button class="btn btn-sm btn-outline-danger ms-2 delete-btn" data-name="${file.name}">🗑️ 刪除</button>
                    </td>
                `;
                tableBody.appendChild(row);
            });
        } catch (err) {
            console.error("載入模型清單失敗:", err);
        }
    }

    // 綁定操作按鈕事件
    tableBody.addEventListener("click", async function (e) {
        if (e.target.classList.contains("rename-btn")) {
            const oldName = e.target.getAttribute("data-old");
            const newName = prompt("請輸入新的模型名稱（不含副檔名）", oldName);
            if (newName && newName !== oldName) {
                let resp = await fetch("/api/rename_checkpoint/", {
                    method: "PUT",
                    headers: { "Content-Type": "application/json", "X-CSRFToken": "{{ csrf_token }}" },
                    body: JSON.stringify({ old_name: oldName, new_name: newName })
                });
                let result = await resp.json();
                if (result.status === "success") {
                    alert("✅ 修改成功！");
                    loadWeights();
                } else {
                    alert("❌ 修改失敗：" + result.error);
                }
            }
        }

        if (e.target.classList.contains("delete-btn")) {
            const filename = e.target.getAttribute("data-name");
            if (confirm(`確定要刪除模型「${filename}.h5」嗎？`)) {
                let resp = await fetch("/api/delete_checkpoint/", {
                    method: "DELETE",
                    headers: { "Content-Type": "application/json", "X-CSRFToken": "{{ csrf_token }}" },
                    body: JSON.stringify({ filenames: [filename] })
                });
                let result = await resp.json();
                if (result.status === "success") {
                    alert("✅ 刪除成功");
                    loadWeights();
                } else {
                    alert("❌ 刪除失敗：" + result.error);
                }
            }
        }
    });

    // 頁面載入時立即呼叫 API
    loadWeights();
});