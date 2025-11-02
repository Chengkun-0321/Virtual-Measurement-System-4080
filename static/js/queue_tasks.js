document.addEventListener("DOMContentLoaded", function() {
    const runningList = document.getElementById("running-tasks");
    const waitingList = document.getElementById("waiting-tasks");

    async function loadTasks() {
        try {
            const response = await fetch("/api/tasks/");
            if (!response.ok) {
                throw new Error("API 請求失敗：" + response.status);
            }
            const data = await response.json();

            runningList.innerHTML = "";
            waitingList.innerHTML = "";

            if (!data.running || data.running.length === 0) {
                runningList.innerHTML = "<li><span class='text-muted'>目前沒有執行中的任務</span></li>";
            } else {
                data.running.forEach(task => {
                    const li = document.createElement("li");
                    li.innerHTML = `🔹 ${task.name} <span class="badge bg-success">執行中</span>`;
                    runningList.appendChild(li);
                });
            }

            if (!data.waiting || data.waiting.length === 0) {
                waitingList.innerHTML = "<li><span class='text-muted'>目前沒有等待的任務</span></li>";
            } else {
                data.waiting.forEach(task => {
                    const li = document.createElement("li");
                    li.innerHTML = `🔹 ${task.name} <span class="badge bg-warning text-dark">等待中</span>`;
                    waitingList.appendChild(li);
                });
            }

        } catch (err) {
            console.error("載入任務失敗：", err);
            runningList.innerHTML = "<li><span class='text-danger'>無法取得任務資料</span></li>";
            waitingList.innerHTML = "";
        }
    }

    // 當使用者打開下拉式選單時才載入最新狀態
    const dropdown = document.getElementById("queueDropdown");
    dropdown.addEventListener("click", loadTasks);
});