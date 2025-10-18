document.addEventListener("DOMContentLoaded", function() {
    const runningList = document.getElementById("running-tasks");
    const waitingList = document.getElementById("waiting-tasks");

    // 假資料（之後可換成 Django API）
    const tasks = [
        { id: "task1", name: "訓練模型 A", status: "running" },
        { id: "task2", name: "測試模型 B", status: "waiting" },
        { id: "task3", name: "預測資料 C", status: "waiting" }
    ];

    // 清空列表
    runningList.innerHTML = "";
    waitingList.innerHTML = "";

    const runningTasks = tasks.filter(t => t.status === "running");
    const waitingTasks = tasks.filter(t => t.status === "waiting");

    if (runningTasks.length === 0) {
        runningList.innerHTML = "<li><span class='text-muted'>目前沒有執行中的任務</span></li>";
    } else {
        runningTasks.forEach(task => {
            const li = document.createElement("li");
            li.classList.add("mb-1");
            li.innerHTML = `🔹 ${task.name} <span class="badge bg-success">執行中</span>`;
            runningList.appendChild(li);
        });
    }

    if (waitingTasks.length === 0) {
        waitingList.innerHTML = "<li><span class='text-muted'>目前沒有等待的任務</span></li>";
    } else {
        waitingTasks.forEach(task => {
            const li = document.createElement("li");
            li.classList.add("mb-1");
            li.innerHTML = `🔹 ${task.name} <span class="badge bg-warning text-dark">等待中</span>`;
            waitingList.appendChild(li);
        });
    }
});