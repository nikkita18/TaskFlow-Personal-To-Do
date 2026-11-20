/**
 * Loopa / TaskFlow Application Controller
 * Handles Memphis Landing Page navigation, Auth Modal, and Task Workspace.
 * 100% Vanilla ES2020+, XSS-safe (DOM createElement + textContent), Accessible.
 */

document.addEventListener("DOMContentLoaded", () => {
  // Views & Containers
  const landingView = document.getElementById("landing-view");
  const appView = document.getElementById("app-view");
  const toastContainer = document.getElementById("toast-container");

  // Nav Elements
  const navAuthGuest = document.getElementById("nav-auth-guest");
  const navAuthUser = document.getElementById("nav-auth-user");
  const navUserName = document.getElementById("nav-user-name");
  const btnNavSignin = document.getElementById("btn-nav-signin");
  const btnNavStart = document.getElementById("btn-nav-start");
  const btnNavDashboard = document.getElementById("btn-nav-dashboard");
  const btnNavLogout = document.getElementById("btn-nav-logout");
  const btnBackToLanding = document.getElementById("btn-back-to-landing");

  // Hero & Landing Action Buttons
  const btnHeroPrimary = document.getElementById("btn-hero-primary");
  const btnHeroSecondary = document.getElementById("btn-hero-secondary");
  const btnBottomStart = document.getElementById("btn-bottom-start");

  // Auth Modal Elements
  const authModal = document.getElementById("auth-modal");
  const tabLogin = document.getElementById("tab-login");
  const tabRegister = document.getElementById("tab-register");
  const loginForm = document.getElementById("login-form");
  const registerForm = document.getElementById("register-form");
  const authAlert = document.getElementById("auth-alert");
  const btnQuickDemo = document.getElementById("btn-quick-demo");
  const btnCloseAuthModal = document.querySelector(".btn-close-auth-modal");

  // Workspace / Task View Elements
  const userDisplay = document.getElementById("user-display");
  const btnLogout = document.getElementById("btn-logout");
  const btnOpenAddTask = document.getElementById("btn-open-add-task");
  const searchInput = document.getElementById("search-input");
  const filterChips = document.querySelectorAll(".filter-chip");
  const filterPriority = document.getElementById("filter-priority");
  const sortBySelect = document.getElementById("sort-by");
  const taskList = document.getElementById("task-list");
  const loadingState = document.getElementById("loading-state");
  const emptyState = document.getElementById("empty-state");
  const errorState = document.getElementById("error-state");
  const errorMessage = document.getElementById("error-message");
  const btnRetryTasks = document.getElementById("btn-retry-tasks");

  // Stats Elements
  const statTotal = document.getElementById("stat-total");
  const statOpen = document.getElementById("stat-open");
  const statDone = document.getElementById("stat-done");
  const statOverdue = document.getElementById("stat-overdue");

  // Modal: Add / Edit
  const taskModal = document.getElementById("task-modal");
  const modalTaskTitle = document.getElementById("modal-task-title");
  const taskForm = document.getElementById("task-form");
  const taskEditId = document.getElementById("task-edit-id");
  const taskTitle = document.getElementById("task-title");
  const taskDesc = document.getElementById("task-desc");
  const taskDueDate = document.getElementById("task-due-date");
  const taskPriority = document.getElementById("task-priority");
  const btnSaveTask = document.getElementById("btn-save-task");

  // Modal: Delete
  const deleteModal = document.getElementById("delete-modal");
  const deletePreview = document.getElementById("delete-task-title-preview");
  const btnConfirmDelete = document.getElementById("btn-confirm-delete");

  // Modal: Change Password
  const pwModal = document.getElementById("pw-modal");
  const btnOpenChangePw = document.getElementById("btn-open-change-pw");
  const changePwForm = document.getElementById("change-pw-form");
  const oldPwInput = document.getElementById("old-pw");
  const newPwInput = document.getElementById("new-pw");

  // ----------------------------------------------------
  // Toast Notifications (Memphis Tactile)
  // ----------------------------------------------------
  function showToast(message, type = "info", duration = 3500) {
    const toast = document.createElement("div");
    toast.className = `toast toast-${type}`;
    toast.setAttribute("role", "status");

    const text = document.createElement("span");
    text.textContent = message;
    toast.appendChild(text);

    toastContainer.appendChild(toast);

    setTimeout(() => {
      toast.style.opacity = "0";
      toast.style.transform = "translateY(-10px)";
      toast.style.transition = "all 0.25s ease";
      setTimeout(() => toast.remove(), 250);
    }, duration);
  }

  // ----------------------------------------------------
  // Auth Modal Management
  // ----------------------------------------------------
  function openAuthModal(isRegister = false) {
    switchAuthTab(isRegister);
    authModal.classList.remove("hidden");
    const inputToFocus = isRegister
      ? document.getElementById("reg-email")
      : document.getElementById("login-email");
    if (inputToFocus) inputToFocus.focus();
  }

  function closeAuthModal() {
    authModal.classList.add("hidden");
  }

  if (btnCloseAuthModal) {
    btnCloseAuthModal.addEventListener("click", closeAuthModal);
  }

  function switchAuthTab(isRegister) {
    authAlert.classList.add("hidden");
    clearFormErrors(loginForm);
    clearFormErrors(registerForm);

    if (isRegister) {
      tabRegister.classList.add("active");
      tabRegister.setAttribute("aria-selected", "true");
      tabLogin.classList.remove("active");
      tabLogin.setAttribute("aria-selected", "false");
      registerForm.classList.remove("hidden");
      loginForm.classList.add("hidden");
    } else {
      tabLogin.classList.add("active");
      tabLogin.setAttribute("aria-selected", "true");
      tabRegister.classList.remove("active");
      tabRegister.setAttribute("aria-selected", "false");
      loginForm.classList.remove("hidden");
      registerForm.classList.add("hidden");
    }
  }

  tabLogin.addEventListener("click", () => switchAuthTab(false));
  tabRegister.addEventListener("click", () => switchAuthTab(true));

  // Trigger Auth Modal from Landing Page CTAs
  if (btnNavSignin) btnNavSignin.addEventListener("click", () => openAuthModal(false));
  if (btnNavStart) btnNavStart.addEventListener("click", () => openAuthModal(true));
  if (btnHeroPrimary) btnHeroPrimary.addEventListener("click", () => {
    if (API.getToken()) {
      showWorkspaceView();
    } else {
      openAuthModal(true);
    }
  });
  if (btnHeroSecondary) btnHeroSecondary.addEventListener("click", () => {
    if (API.getToken()) {
      showWorkspaceView();
    } else {
      openAuthModal(false);
    }
  });
  if (btnBottomStart) btnBottomStart.addEventListener("click", () => {
    if (API.getToken()) {
      showWorkspaceView();
    } else {
      openAuthModal(true);
    }
  });

  // Password Visibility Toggle
  document.querySelectorAll(".btn-toggle-pw").forEach((btn) => {
    btn.addEventListener("click", () => {
      const targetId = btn.getAttribute("data-target");
      const input = document.getElementById(targetId);
      if (input) {
        if (input.type === "password") {
          input.type = "text";
          btn.textContent = "🙈";
        } else {
          input.type = "password";
          btn.textContent = "👁";
        }
      }
    });
  });

  // 1-Click Demo Login
  if (btnQuickDemo) {
    btnQuickDemo.addEventListener("click", () => {
      switchAuthTab(false);
      document.getElementById("login-email").value = "demo@taskflow.dev";
      document.getElementById("login-password").value = "Password123";
      loginForm.requestSubmit();
    });
  }

  // ----------------------------------------------------
  // Form Error Display Helpers
  // ----------------------------------------------------
  function clearFormErrors(form) {
    form.querySelectorAll(".field-error").forEach((el) => (el.textContent = ""));
    form.querySelectorAll(".form-input").forEach((el) => (el.style.borderColor = ""));
  }

  function displayFormErrors(form, errors) {
    clearFormErrors(form);
    if (!errors) return;
    for (const [field, message] of Object.entries(errors)) {
      const errEl = form.querySelector(`#${field}-error`) || form.querySelector(`[id$="-${field}-error"]`);
      const inputEl = form.querySelector(`[name="${field}"]`) || form.querySelector(`#${field}`);
      if (errEl) errEl.textContent = message;
      if (inputEl) inputEl.style.borderColor = "var(--coral)";
    }
  }

  // ----------------------------------------------------
  // Auth Form Submissions (Login & Register)
  // ----------------------------------------------------
  loginForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    clearFormErrors(loginForm);
    authAlert.classList.add("hidden");

    const email = document.getElementById("login-email").value.trim();
    const password = document.getElementById("login-password").value;

    let hasErr = false;
    if (!email) {
      document.getElementById("login-email-error").textContent = "Email is required";
      hasErr = true;
    }
    if (!password) {
      document.getElementById("login-password-error").textContent = "Password is required";
      hasErr = true;
    }
    if (hasErr) return;

    const btnSubmit = document.getElementById("btn-login-submit");
    btnSubmit.disabled = true;
    btnSubmit.querySelector(".btn-text").textContent = "Signing In...";
    btnSubmit.querySelector(".spinner").classList.remove("hidden");

    try {
      await API.login(email, password);
      showToast("Welcome back! Signed in.", "success");
      closeAuthModal();
      await initializeSession();
      showWorkspaceView();
    } catch (err) {
      if (err.errors) {
        displayFormErrors(loginForm, err.errors);
      } else {
        authAlert.textContent = err.error || "Login failed. Please check your credentials.";
        authAlert.classList.remove("hidden");
      }
    } finally {
      btnSubmit.disabled = false;
      btnSubmit.querySelector(".btn-text").textContent = "Sign In";
      btnSubmit.querySelector(".spinner").classList.add("hidden");
    }
  });

  registerForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    clearFormErrors(registerForm);
    authAlert.classList.add("hidden");

    const name = document.getElementById("reg-name").value.trim();
    const email = document.getElementById("reg-email").value.trim();
    const password = document.getElementById("reg-password").value;

    let hasErr = false;
    if (!email) {
      document.getElementById("reg-email-error").textContent = "Email is required";
      hasErr = true;
    }
    if (!password || password.length < 8) {
      document.getElementById("reg-password-error").textContent = "Password must be at least 8 characters";
      hasErr = true;
    }
    if (hasErr) return;

    const btnSubmit = document.getElementById("btn-register-submit");
    btnSubmit.disabled = true;
    btnSubmit.querySelector(".btn-text").textContent = "Creating Account...";
    btnSubmit.querySelector(".spinner").classList.remove("hidden");

    try {
      await API.register(email, password, name);
      // Auto login
      await API.login(email, password);
      showToast("Account created! Welcome to Loopa.", "success");
      closeAuthModal();
      await initializeSession();
      showWorkspaceView();
    } catch (err) {
      if (err.errors) {
        displayFormErrors(registerForm, err.errors);
      } else {
        authAlert.textContent = err.error || "Registration failed.";
        authAlert.classList.remove("hidden");
      }
    } finally {
      btnSubmit.disabled = false;
      btnSubmit.querySelector(".btn-text").textContent = "Create Account";
      btnSubmit.querySelector(".spinner").classList.add("hidden");
    }
  });

  // ----------------------------------------------------
  // Logout & 401 Session Expiration
  // ----------------------------------------------------
  async function handleLogout() {
    try {
      await API.logout();
    } catch (e) {
      // Ignore network errors on logout
    }
    AppState.setUser(null);
    AppState.setTasks([]);
    updateNavState(false);
    showLandingView();
    showToast("Signed out successfully.", "info");
  }

  if (btnLogout) btnLogout.addEventListener("click", handleLogout);
  if (btnNavLogout) btnNavLogout.addEventListener("click", handleLogout);

  API.onUnauthorized(() => {
    AppState.setUser(null);
    AppState.setTasks([]);
    updateNavState(false);
    showLandingView();
    openAuthModal(false);
    authAlert.textContent = "Your session expired. Please sign in again.";
    authAlert.classList.remove("hidden");
  });

  // ----------------------------------------------------
  // View Transitions (Landing vs Workspace)
  // ----------------------------------------------------
  function showLandingView() {
    appView.classList.add("hidden");
    landingView.classList.remove("hidden");
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  function showWorkspaceView() {
    landingView.classList.add("hidden");
    appView.classList.remove("hidden");
    window.scrollTo({ top: 0, behavior: "smooth" });
    loadTasks();
  }

  if (btnNavDashboard) btnNavDashboard.addEventListener("click", showWorkspaceView);
  if (btnBackToLanding) btnBackToLanding.addEventListener("click", showLandingView);

  function updateNavState(isLoggedIn, user = null) {
    if (isLoggedIn && user) {
      navAuthGuest.classList.add("hidden");
      navAuthUser.classList.remove("hidden");
      const displayName = user.name ? user.name.split(" ")[0] : user.email.split("@")[0];
      navUserName.textContent = displayName;
      userDisplay.textContent = user.name ? `${user.name} (${user.email})` : user.email;
    } else {
      navAuthGuest.classList.remove("hidden");
      navAuthUser.classList.add("hidden");
      userDisplay.textContent = "";
    }
  }

  // ----------------------------------------------------
  // Task Data Fetching & Rendering (Strictly XSS Safe)
  // ----------------------------------------------------
  async function loadTasks() {
    loadingState.classList.remove("hidden");
    emptyState.classList.add("hidden");
    errorState.classList.add("hidden");
    taskList.innerHTML = "";

    try {
      const filters = AppState.getState().filters;
      const tasks = await API.getTasks(filters);
      AppState.setTasks(tasks);
      renderTasks(tasks);
      updateStats(tasks);
    } catch (err) {
      loadingState.classList.add("hidden");
      errorState.classList.remove("hidden");
      errorMessage.textContent = err.error || "Failed to load tasks.";
    }
  }

  btnRetryTasks.addEventListener("click", loadTasks);

  function getTodayString() {
    const today = new Date();
    const yyyy = today.getFullYear();
    const mm = String(today.getMonth() + 1).padStart(2, "0");
    const dd = String(today.getDate()).padStart(2, "0");
    return `${yyyy}-${mm}-${dd}`;
  }

  function renderTasks(tasks) {
    loadingState.classList.add("hidden");
    taskList.innerHTML = "";

    if (!tasks || tasks.length === 0) {
      emptyState.classList.remove("hidden");
      return;
    }
    emptyState.classList.add("hidden");

    const todayStr = getTodayString();

    tasks.forEach((task) => {
      const isOverdue = task.dueDate && task.dueDate < todayStr && !task.done;

      // Card element
      const li = document.createElement("li");
      li.className = `task-card ${task.done ? "is-done" : ""} ${isOverdue ? "is-overdue" : ""}`;
      li.setAttribute("data-id", task.id);

      // Checkbox container
      const checkWrapper = document.createElement("label");
      checkWrapper.className = "task-check-wrapper";
      checkWrapper.setAttribute("title", task.done ? "Mark as open" : "Mark as done");

      const checkbox = document.createElement("input");
      checkbox.type = "checkbox";
      checkbox.className = "task-checkbox";
      checkbox.checked = Boolean(task.done);
      checkbox.setAttribute("aria-label", `Mark task "${task.title}" as complete`);
      checkbox.addEventListener("change", () => toggleTaskDone(task));

      checkWrapper.appendChild(checkbox);
      li.appendChild(checkWrapper);

      // Task content container
      const content = document.createElement("div");
      content.className = "task-content";

      // Header row
      const headerRow = document.createElement("div");
      headerRow.className = "task-header-row";

      const titleEl = document.createElement("h3");
      titleEl.className = "task-title-text";
      titleEl.textContent = task.title; // Safe against XSS

      headerRow.appendChild(titleEl);
      content.appendChild(headerRow);

      // Description (if present)
      if (task.description && task.description.trim()) {
        const descEl = document.createElement("p");
        descEl.className = "task-desc-text";
        descEl.textContent = task.description; // Safe against XSS
        content.appendChild(descEl);
      }

      // Meta row (Priority, Due Date, Overdue Badge)
      const metaRow = document.createElement("div");
      metaRow.className = "task-meta-row";

      // Priority badge
      const priorityBadge = document.createElement("span");
      priorityBadge.className = `badge badge-priority-${task.priority}`;
      priorityBadge.textContent = task.priority;
      metaRow.appendChild(priorityBadge);

      // Due date badge
      if (task.dueDate) {
        const dueBadge = document.createElement("span");
        dueBadge.className = `badge-due ${isOverdue ? "is-overdue-text" : ""}`;
        dueBadge.textContent = isOverdue ? `⚠️ Overdue (${task.dueDate})` : `📅 Due ${task.dueDate}`;
        metaRow.appendChild(dueBadge);
      }

      content.appendChild(metaRow);
      li.appendChild(content);

      // Action buttons (Edit & Delete)
      const actions = document.createElement("div");
      actions.className = "task-actions";

      const btnEdit = document.createElement("button");
      btnEdit.type = "button";
      btnEdit.className = "btn-task-action";
      btnEdit.setAttribute("aria-label", `Edit task "${task.title}"`);
      btnEdit.title = "Edit task";
      btnEdit.textContent = "✏️";
      btnEdit.addEventListener("click", () => openEditModal(task));
      actions.appendChild(btnEdit);

      const btnDelete = document.createElement("button");
      btnDelete.type = "button";
      btnDelete.className = "btn-task-action delete";
      btnDelete.setAttribute("aria-label", `Delete task "${task.title}"`);
      btnDelete.title = "Delete task";
      btnDelete.textContent = "🗑️";
      btnDelete.addEventListener("click", () => openDeleteModal(task));
      actions.appendChild(btnDelete);

      li.appendChild(actions);
      taskList.appendChild(li);
    });
  }

  function updateStats(tasks) {
    const total = tasks.length;
    const completed = tasks.filter((t) => t.done).length;
    const open = total - completed;
    const todayStr = getTodayString();
    const overdue = tasks.filter((t) => t.dueDate && t.dueDate < todayStr && !t.done).length;

    statTotal.textContent = `Total: ${total}`;
    statOpen.textContent = `Open: ${open}`;
    statDone.textContent = `Completed: ${completed}`;

    if (overdue > 0) {
      statOverdue.textContent = `⚠️ Overdue: ${overdue}`;
      statOverdue.classList.remove("hidden");
    } else {
      statOverdue.classList.add("hidden");
    }
  }

  // ----------------------------------------------------
  // Task Actions: Toggle Done, Add, Edit, Delete
  // ----------------------------------------------------
  async function toggleTaskDone(task) {
    const newDone = !task.done;
    try {
      const updated = await API.patchTask(task.id, { done: newDone });
      AppState.updateSingleTask(updated);
      showToast(newDone ? "Task marked completed!" : "Task marked as open.", "info");
      loadTasks();
    } catch (err) {
      showToast(err.error || "Failed to update task status", "error");
      loadTasks();
    }
  }

  function openAddModal() {
    AppState.setEditingTaskId(null);
    modalTaskTitle.textContent = "Add New Task";
    taskForm.reset();
    clearFormErrors(taskForm);
    taskEditId.value = "";
    taskPriority.value = "medium";
    taskModal.classList.remove("hidden");
    taskTitle.focus();
  }

  function openEditModal(task) {
    AppState.setEditingTaskId(task.id);
    modalTaskTitle.textContent = "Edit Task";
    clearFormErrors(taskForm);
    taskEditId.value = task.id;
    taskTitle.value = task.title;
    taskDesc.value = task.description || "";
    taskDueDate.value = task.dueDate || "";
    taskPriority.value = task.priority || "medium";
    taskModal.classList.remove("hidden");
    taskTitle.focus();
  }

  function closeTaskModal() {
    taskModal.classList.add("hidden");
  }

  btnOpenAddTask.addEventListener("click", openAddModal);
  document.querySelectorAll(".btn-close-modal").forEach((btn) => {
    btn.addEventListener("click", closeTaskModal);
  });

  taskForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    clearFormErrors(taskForm);

    const title = taskTitle.value.trim();
    const description = taskDesc.value.trim();
    const dueDate = taskDueDate.value || null;
    const priority = taskPriority.value;
    const editId = taskEditId.value;

    if (!title) {
      document.getElementById("task-title-error").textContent = "Title is required";
      return;
    }

    btnSaveTask.disabled = true;
    btnSaveTask.querySelector(".btn-text").textContent = "Saving...";
    btnSaveTask.querySelector(".spinner").classList.remove("hidden");

    try {
      if (editId) {
        await API.patchTask(editId, { title, description, dueDate, priority });
        showToast("Task updated successfully!", "success");
      } else {
        await API.createTask({ title, description, dueDate, priority });
        showToast("Task created successfully!", "success");
      }
      closeTaskModal();
      await loadTasks();
    } catch (err) {
      if (err.errors) {
        displayFormErrors(taskForm, err.errors);
      } else {
        showToast(err.error || "Failed to save task", "error");
      }
    } finally {
      btnSaveTask.disabled = false;
      btnSaveTask.querySelector(".btn-text").textContent = "Save Task";
      btnSaveTask.querySelector(".spinner").classList.add("hidden");
    }
  });

  // Delete Modal
  function openDeleteModal(task) {
    AppState.setDeletingTask(task);
    deletePreview.textContent = task.title;
    deleteModal.classList.remove("hidden");
    btnConfirmDelete.focus();
  }

  function closeDeleteModal() {
    deleteModal.classList.add("hidden");
    AppState.setDeletingTask(null);
  }

  document.querySelectorAll(".btn-close-delete-modal").forEach((btn) => {
    btn.addEventListener("click", closeDeleteModal);
  });

  btnConfirmDelete.addEventListener("click", async () => {
    const deletingTask = AppState.getState().deletingTask;
    if (!deletingTask) return;

    btnConfirmDelete.disabled = true;
    try {
      await API.deleteTask(deletingTask.id);
      showToast("Task deleted", "info");
      closeDeleteModal();
      await loadTasks();
    } catch (err) {
      showToast(err.error || "Failed to delete task", "error");
    } finally {
      btnConfirmDelete.disabled = false;
    }
  });

  // Change Password Modal
  btnOpenChangePw.addEventListener("click", () => {
    changePwForm.reset();
    clearFormErrors(changePwForm);
    pwModal.classList.remove("hidden");
    oldPwInput.focus();
  });

  function closePwModal() {
    pwModal.classList.add("hidden");
  }

  document.querySelectorAll(".btn-close-pw-modal").forEach((btn) => {
    btn.addEventListener("click", closePwModal);
  });

  changePwForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    clearFormErrors(changePwForm);

    const oldPw = oldPwInput.value;
    const newPw = newPwInput.value;

    let hasErr = false;
    if (!oldPw) {
      document.getElementById("old-pw-error").textContent = "Current password is required";
      hasErr = true;
    }
    if (!newPw || newPw.length < 8) {
      document.getElementById("new-pw-error").textContent = "New password must be at least 8 characters";
      hasErr = true;
    }
    if (hasErr) return;

    const btnSubmit = document.getElementById("btn-submit-change-pw");
    btnSubmit.disabled = true;

    try {
      await API.changePassword(oldPw, newPw);
      showToast("Password updated successfully!", "success");
      closePwModal();
    } catch (err) {
      if (err.errors) {
        displayFormErrors(changePwForm, err.errors);
      } else {
        document.getElementById("old-pw-error").textContent = err.error || "Failed to update password";
      }
    } finally {
      btnSubmit.disabled = false;
    }
  });

  // ----------------------------------------------------
  // Filters, Debounced Search, and Sorting Handlers
  // ----------------------------------------------------
  filterChips.forEach((chip) => {
    chip.addEventListener("click", () => {
      filterChips.forEach((c) => c.classList.remove("active"));
      chip.classList.add("active");
      const status = chip.getAttribute("data-status");
      AppState.setFilter("status", status);
      loadTasks();
    });
  });

  filterPriority.addEventListener("change", (e) => {
    AppState.setFilter("priority", e.target.value);
    loadTasks();
  });

  sortBySelect.addEventListener("change", (e) => {
    const [sort, order] = e.target.value.split("-");
    AppState.setFilter("sort", sort);
    AppState.setFilter("order", order);
    loadTasks();
  });

  // Debounced search input (300ms)
  let searchTimeout = null;
  searchInput.addEventListener("input", (e) => {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(() => {
      AppState.setFilter("q", e.target.value.trim());
      loadTasks();
    }, 300);
  });

  // Global ESC key to close open modals
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
      closeAuthModal();
      closeTaskModal();
      closeDeleteModal();
      closePwModal();
    }
  });

  // ----------------------------------------------------
  // Session Initialization
  // ----------------------------------------------------
  async function initializeSession() {
    const token = API.getToken();
    if (!token) {
      updateNavState(false);
      return;
    }

    try {
      const user = await API.getMe();
      AppState.setUser(user);
      updateNavState(true, user);
    } catch (err) {
      updateNavState(false);
    }
  }

  // Register PWA service worker if supported
  if ("serviceWorker" in navigator) {
    navigator.serviceWorker
      .register("/sw.js")
      .catch((err) => console.log("ServiceWorker registration skipped:", err));
  }

  // Start by initializing current session state
  initializeSession();
});
