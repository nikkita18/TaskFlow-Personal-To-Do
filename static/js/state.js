/**
 * TaskFlow Application State Manager
 */

const AppState = (() => {
  const state = {
    currentUser: null,
    tasks: [],
    filters: {
      status: "all",
      priority: "",
      q: "",
      sort: "createdAt",
      order: "desc",
    },
    editingTaskId: null,
    deletingTask: null,
    theme: localStorage.getItem("taskflow_theme") || "dark",
  };

  const listeners = [];

  function subscribe(listener) {
    listeners.push(listener);
    return () => {
      const idx = listeners.indexOf(listener);
      if (idx !== -1) listeners.splice(idx, 1);
    };
  }

  function notify(event, payload) {
    listeners.forEach((listener) => {
      try {
        listener(event, payload, state);
      } catch (e) {
        console.error("State listener error:", e);
      }
    });
  }

  return {
    getState() {
      return state;
    },
    subscribe,

    setUser(user) {
      state.currentUser = user;
      notify("USER_CHANGED", user);
    },

    setTasks(tasks) {
      state.tasks = Array.isArray(tasks) ? tasks : [];
      notify("TASKS_UPDATED", state.tasks);
    },

    updateSingleTask(updatedTask) {
      const idx = state.tasks.findIndex((t) => t.id === updatedTask.id);
      if (idx !== -1) {
        state.tasks[idx] = updatedTask;
      }
      notify("TASKS_UPDATED", state.tasks);
    },

    removeSingleTask(taskId) {
      state.tasks = state.tasks.filter((t) => t.id !== taskId);
      notify("TASKS_UPDATED", state.tasks);
    },

    setFilter(key, value) {
      state.filters[key] = value;
      notify("FILTERS_CHANGED", state.filters);
    },

    setEditingTaskId(id) {
      state.editingTaskId = id;
    },

    setDeletingTask(task) {
      state.deletingTask = task;
    },

    setTheme(theme) {
      state.theme = theme;
      localStorage.setItem("taskflow_theme", theme);
      document.documentElement.setAttribute("data-theme", theme);
      notify("THEME_CHANGED", theme);
    },
  };
})();
