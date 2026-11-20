/**
 * TaskFlow: Simple & Beginner-Friendly JavaScript
 * Easy to read, easy to modify during live interviews!
 */

// Global variable to hold tasks in memory
let currentTasks = [];
let editingTaskId = null;
let deletingTaskId = null;

// ==========================================
// 1. SIMPLE API HELPER (Fetch data from Python)
// ==========================================
async function api(url, method = "GET", bodyData = null) {
  const token = localStorage.getItem("token");
  const options = {
    method: method,
    headers: { "Content-Type": "application/json" }
  };

  // Add Bearer token header if user is logged in
  if (token) {
    options.headers["Authorization"] = "Bearer " + token;
  }

  // Add JSON body if sending data (POST or PATCH)
  if (bodyData) {
    options.body = JSON.stringify(bodyData);
  }

  const response = await fetch(url, options);

  // If token is invalid or expired (401), send user to login
  if (response.status === 401) {
    localStorage.removeItem("token");
    showAuth("Session expired. Please log in again.");
    return null;
  }

  if (response.status === 204) {
    return true; // 204 No Content (successful delete or logout)
  }

  const data = await response.json();
  if (!response.ok) {
    // If backend returned error, throw it so catch() handles it
    throw data;
  }
  return data;
}

// ==========================================
// 2. VIEW SWITCHING (Auth Screen vs Tasks Screen)
// ==========================================
function showAuth(message = "") {
  document.getElementById("auth-view").classList.remove("hidden");
  document.getElementById("app-view").classList.add("hidden");
  const alertBox = document.getElementById("auth-alert");
  if (message) {
    alertBox.textContent = message;
    alertBox.classList.remove("hidden");
  } else {
    alertBox.classList.add("hidden");
  }
}

function showTasks() {
  document.getElementById("auth-view").classList.add("hidden");
  document.getElementById("app-view").classList.remove("hidden");
  loadTasks();
}

// Switch between "Sign In" and "Create Account" tabs
function switchAuthTab(isRegister) {
  document.getElementById("tab-login").classList.toggle("active", !isRegister);
  document.getElementById("tab-register").classList.toggle("active", isRegister);
  document.getElementById("login-form").classList.toggle("hidden", isRegister);
  document.getElementById("register-form").classList.toggle("hidden", !isRegister);
  document.getElementById("auth-alert").classList.add("hidden");
}

// Toast popup message helper
function showToast(message) {
  const container = document.getElementById("toast-container");
  const toast = document.createElement("div");
  toast.className = "toast";
  toast.textContent = message;
  container.appendChild(toast);
  setTimeout(() => toast.remove(), 2500);
}

// ==========================================
// 3. AUTHENTICATION (Login, Register, Logout)
// ==========================================

// Handle Login
async function handleLogin(e) {
  e.preventDefault();
  const email = document.getElementById("login-email").value.trim();
  const password = document.getElementById("login-password").value;

  try {
    const res = await api("/api/auth/login", "POST", { email, password });
    localStorage.setItem("token", res.token);
    showToast("Signed in successfully!");
    checkUserSession();
  } catch (err) {
    showAuth(err.error || "Login failed. Check your email/password.");
  }
}

// Handle Register (Create Account)
async function handleRegister(e) {
  e.preventDefault();
  const name = document.getElementById("reg-name").value.trim();
  const email = document.getElementById("reg-email").value.trim();
  const password = document.getElementById("reg-password").value;

  try {
    await api("/api/auth/register", "POST", { email, password, name });
    // Auto login after registration
    const res = await api("/api/auth/login", "POST", { email, password });
    localStorage.setItem("token", res.token);
    showToast("Account created!");
    checkUserSession();
  } catch (err) {
    if (err.errors) {
      // Show first error message if validation failed
      const msg = Object.values(err.errors).join(". ");
      showAuth(msg);
    } else {
      showAuth(err.error || "Registration failed.");
    }
  }
}

// Handle Logout
async function handleLogout() {
  try {
    await api("/api/auth/logout", "POST");
  } catch (err) {
    // Ignore error on logout
  }
  localStorage.removeItem("token");
  showToast("Logged out");
  showAuth("You have been logged out.");
}

// Quick 1-Click Demo Login
function fillDemoLogin() {
  switchAuthTab(false);
  document.getElementById("login-email").value = "demo@taskflow.dev";
  document.getElementById("login-password").value = "Password123";
  document.getElementById("login-form").requestSubmit();
}

// Check if user is already logged in on page load
async function checkUserSession() {
  const token = localStorage.getItem("token");
  if (!token) {
    showAuth();
    return;
  }

  try {
    const user = await api("/api/auth/me");
    if (user) {
      document.getElementById("user-display").textContent = user.name ? `${user.name} (${user.email})` : user.email;
      showTasks();
    }
  } catch (err) {
    showAuth("Please sign in.");
  }
}

// ==========================================
// 4. TASK MANAGEMENT (Fetch, Add, Edit, Delete)
// ==========================================

// Helper: Check if task is overdue
function isOverdue(task) {
  if (!task.dueDate || task.done) return false;
  const today = new Date().toISOString().split("T")[0];
  return task.dueDate < today;
}

// Load tasks from backend with filters
async function loadTasks() {
  const status = document.querySelector(".filter-chip.active").getAttribute("data-status");
  const priority = document.getElementById("filter-priority").value;
  const sortValue = document.getElementById("sort-by").value; // e.g. "createdAt-desc"
  const [sort, order] = sortValue.split("-");
  const q = document.getElementById("search-input").value.trim();

  // Build query string e.g. ?status=open&sort=dueDate&order=asc
  let query = `/api/tasks?status=${status}&sort=${sort}&order=${order}`;
  if (priority) query += `&priority=${priority}`;
  if (q) query += `&q=${encodeURIComponent(q)}`;

  try {
    document.getElementById("loading-state").classList.remove("hidden");
    document.getElementById("empty-state").classList.add("hidden");
    document.getElementById("error-state").classList.add("hidden");

    currentTasks = await api(query);
    renderTaskList(currentTasks);
    updateStats(currentTasks);
  } catch (err) {
    document.getElementById("error-state").classList.remove("hidden");
    document.getElementById("error-message").textContent = err.error || "Failed to load tasks.";
  } finally {
    document.getElementById("loading-state").classList.add("hidden");
  }
}

// Render the list of tasks to the DOM
function renderTaskList(tasks) {
  const listEl = document.getElementById("task-list");
  listEl.innerHTML = ""; // Clear current list

  if (!tasks || tasks.length === 0) {
    document.getElementById("empty-state").classList.remove("hidden");
    return;
  }
  document.getElementById("empty-state").classList.add("hidden");

  tasks.forEach((task) => {
    const overdue = isOverdue(task);
    const item = document.createElement("li");
    item.className = `task-card ${task.done ? "is-done" : ""} ${overdue ? "is-overdue" : ""}`;

    item.innerHTML = `
      <label class="task-check-wrapper" title="${task.done ? 'Mark as open' : 'Mark as done'}">
        <input type="checkbox" class="task-checkbox" ${task.done ? "checked" : ""}>
      </label>
      <div class="task-content">
        <div class="task-header-row">
          <h3 class="task-title-text"></h3>
        </div>
        <p class="task-desc-text"></p>
        <div class="task-meta-row">
          <span class="badge badge-priority-${task.priority}">${task.priority}</span>
          ${task.dueDate ? `<span class="badge-due ${overdue ? "is-overdue-text" : ""}">📅 ${overdue ? "⚠️ Overdue: " : "Due: "}${task.dueDate}</span>` : ""}
        </div>
      </div>
      <div class="task-actions">
        <button class="btn-task-action btn-edit" title="Edit">✏️</button>
        <button class="btn-task-action delete btn-del" title="Delete">🗑️</button>
      </div>
    `;

    // Safely insert text to avoid XSS
    item.querySelector(".task-title-text").textContent = task.title;
    item.querySelector(".task-desc-text").textContent = task.description || "";

    // Event: Toggle Checkbox
    item.querySelector(".task-checkbox").addEventListener("change", () => toggleDone(task));

    // Event: Click Edit
    item.querySelector(".btn-edit").addEventListener("click", () => openEditModal(task));

    // Event: Click Delete
    item.querySelector(".btn-del").addEventListener("click", () => openDeleteModal(task));

    listEl.appendChild(item);
  });
}

// Update the statistics numbers
function updateStats(tasks) {
  const total = tasks.length;
  const completed = tasks.filter((t) => t.done).length;
  const open = total - completed;
  const overdueCount = tasks.filter((t) => isOverdue(t)).length;

  document.getElementById("stat-total").textContent = `Total: ${total}`;
  document.getElementById("stat-open").textContent = `Open: ${open}`;
  document.getElementById("stat-done").textContent = `Completed: ${completed}`;

  const overdueEl = document.getElementById("stat-overdue");
  if (overdueCount > 0) {
    overdueEl.textContent = `⚠️ Overdue: ${overdueCount}`;
    overdueEl.classList.remove("hidden");
  } else {
    overdueEl.classList.add("hidden");
  }
}

// Toggle Task Done / Open
async function toggleDone(task) {
  try {
    await api(`/api/tasks/${task.id}`, "PATCH", { done: !task.done });
    loadTasks();
  } catch (err) {
    showToast(err.error || "Failed to update task");
  }
}

// Open "Add Task" Modal
function openAddModal() {
  editingTaskId = null;
  document.getElementById("modal-task-title").textContent = "Add New Task";
  document.getElementById("task-form").reset();
  document.getElementById("task-priority").value = "medium";
  document.getElementById("task-modal").classList.remove("hidden");
  document.getElementById("task-title").focus();
}

// Open "Edit Task" Modal
function openEditModal(task) {
  editingTaskId = task.id;
  document.getElementById("modal-task-title").textContent = "Edit Task";
  document.getElementById("task-title").value = task.title;
  document.getElementById("task-desc").value = task.description || "";
  document.getElementById("task-due-date").value = task.dueDate || "";
  document.getElementById("task-priority").value = task.priority || "medium";
  document.getElementById("task-modal").classList.remove("hidden");
  document.getElementById("task-title").focus();
}

// Save Task (Handles both Add and Edit)
async function handleSaveTask(e) {
  e.preventDefault();
  const title = document.getElementById("task-title").value.trim();
  const description = document.getElementById("task-desc").value.trim();
  const dueDate = document.getElementById("task-due-date").value || null;
  const priority = document.getElementById("task-priority").value;

  if (!title) {
    alert("Title is required!");
    return;
  }

  const payload = { title, description, dueDate, priority };

  try {
    if (editingTaskId) {
      // Editing existing task
      await api(`/api/tasks/${editingTaskId}`, "PATCH", payload);
      showToast("Task updated!");
    } else {
      // Creating new task
      await api("/api/tasks", "POST", payload);
      showToast("Task created!");
    }
    document.getElementById("task-modal").classList.add("hidden");
    loadTasks();
  } catch (err) {
    alert(err.error || "Failed to save task");
  }
}

// Open "Confirm Delete" Modal
function openDeleteModal(task) {
  deletingTaskId = task.id;
  document.getElementById("delete-task-title-preview").textContent = task.title;
  document.getElementById("delete-modal").classList.remove("hidden");
}

// Confirm Delete
async function handleConfirmDelete() {
  if (!deletingTaskId) return;
  try {
    await api(`/api/tasks/${deletingTaskId}`, "DELETE");
    showToast("Task deleted");
    document.getElementById("delete-modal").classList.add("hidden");
    loadTasks();
  } catch (err) {
    alert(err.error || "Failed to delete task");
  }
}

// ==========================================
// 5. EVENT LISTENERS (Page Setup)
// ==========================================
document.addEventListener("DOMContentLoaded", () => {
  // Check session on load
  checkUserSession();

  // Auth Events
  document.getElementById("tab-login").addEventListener("click", () => switchAuthTab(false));
  document.getElementById("tab-register").addEventListener("click", () => switchAuthTab(true));
  document.getElementById("login-form").addEventListener("submit", handleLogin);
  document.getElementById("register-form").addEventListener("submit", handleRegister);
  document.getElementById("btn-logout").addEventListener("click", handleLogout);
  document.getElementById("btn-quick-demo").addEventListener("click", fillDemoLogin);

  // Task Events
  document.getElementById("btn-open-add-task").addEventListener("click", openAddModal);
  document.getElementById("task-form").addEventListener("submit", handleSaveTask);
  document.getElementById("btn-confirm-delete").addEventListener("click", handleConfirmDelete);
  document.getElementById("btn-retry-tasks").addEventListener("click", loadTasks);

  // Close Modals
  document.querySelectorAll(".btn-close-modal").forEach((btn) => {
    btn.addEventListener("click", () => document.getElementById("task-modal").classList.add("hidden"));
  });
  document.querySelectorAll(".btn-close-delete-modal").forEach((btn) => {
    btn.addEventListener("click", () => document.getElementById("delete-modal").classList.add("hidden"));
  });

  // Filter Chips (All, Open, Completed)
  document.querySelectorAll(".filter-chip").forEach((chip) => {
    chip.addEventListener("click", () => {
      document.querySelectorAll(".filter-chip").forEach((c) => c.classList.remove("active"));
      chip.classList.add("active");
      loadTasks();
    });
  });

  // Priority & Sort Dropdowns
  document.getElementById("filter-priority").addEventListener("change", loadTasks);
  document.getElementById("sort-by").addEventListener("change", loadTasks);

  // Live Search
  let searchTimer;
  document.getElementById("search-input").addEventListener("input", () => {
    clearTimeout(searchTimer);
    searchTimer = setTimeout(loadTasks, 300);
  });
});
