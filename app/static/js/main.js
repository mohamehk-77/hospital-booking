const TOKEN_KEY = "rady_token";
const USER_KEY = "rady_user";

const WEEKDAY_NAMES = [
  "الاثنين",
  "الثلاثاء",
  "الأربعاء",
  "الخميس",
  "الجمعة",
  "السبت",
  "الأحد",
];

const STATUS_LABELS = {
  confirmed: "مؤكد",
  cancelled: "ملغي",
  completed: "مكتمل",
};

function readStoredUser() {
  try {
    return JSON.parse(localStorage.getItem(USER_KEY) || "null");
  } catch {
    return null;
  }
}

const state = {
  departments: [],
  doctors: [],
  selectedSlot: null,
  token: localStorage.getItem(TOKEN_KEY),
  user: readStoredUser(),
};

const year = document.getElementById("year");
if (year) {
  year.textContent = new Date().getFullYear();
}

const header = document.querySelector(".site-header");
if (header) {
  const onScroll = () => header.classList.toggle("is-scrolled", window.scrollY > 8);
  window.addEventListener("scroll", onScroll, { passive: true });
  onScroll();
}

const els = {
  department: document.getElementById("booking-department"),
  doctor: document.getElementById("booking-doctor"),
  date: document.getElementById("booking-date"),
  days: document.getElementById("booking-days"),
  slots: document.getElementById("booking-slots"),
  notes: document.getElementById("booking-notes"),
  auth: document.getElementById("auth-box"),
  form: document.getElementById("booking-form"),
  submit: document.getElementById("booking-submit"),
  status: document.getElementById("booking-status"),
  success: document.getElementById("booking-success"),
  successText: document.getElementById("booking-success-text"),
  modal: document.getElementById("appointments-modal"),
  appointmentsList: document.getElementById("appointments-list"),
};

const escapeHtml = (value) =>
  String(value).replace(/[&<>"']/g, (ch) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;",
  }[ch]));

function detailOf(data) {
  if (!data) return "";
  if (typeof data.detail === "string") return data.detail;
  if (Array.isArray(data.detail)) {
    return data.detail.map((item) => item.msg).join("، ");
  }
  return "";
}

async function getJSON(url) {
  const response = await fetch(url, { headers: { Accept: "application/json" } });
  if (!response.ok) {
    throw new Error(`${url} -> ${response.status}`);
  }
  return response.json();
}

async function api(url, options = {}) {
  const headers = new Headers(options.headers || {});
  if (state.token) {
    headers.set("Authorization", `Bearer ${state.token}`);
  }
  const response = await fetch(url, { ...options, headers });
  let data = null;
  try {
    data = await response.json();
  } catch {
    data = null;
  }
  if (!response.ok) {
    const error = new Error(detailOf(data) || `خطأ ${response.status}`);
    error.status = response.status;
    error.data = data;
    throw error;
  }
  return data;
}

function isoDate(date) {
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, "0");
  const d = String(date.getDate()).padStart(2, "0");
  return `${y}-${m}-${d}`;
}

function formatDate(value) {
  const date = new Date(`${value}T00:00:00`);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleDateString("ar-EG", {
    weekday: "long",
    day: "numeric",
    month: "long",
  });
}

function formatTime(value) {
  return String(value).slice(0, 5);
}

function jsToPythonWeekday(jsDay) {
  return (jsDay + 6) % 7;
}

function pickBookingDate(schedules) {
  if (!schedules.length) return null;

  const now = new Date();
  const todayWeekday = jsToPythonWeekday(now.getDay());
  const todayRows = schedules.filter((row) => row.weekday === todayWeekday);

  if (todayRows.length) {
    const latestEnd = todayRows
      .map((row) => row.end_time)
      .sort()
      .pop();
    const [hours, minutes] = latestEnd.split(":").map(Number);
    const end = new Date(now);
    end.setHours(hours, minutes, 0, 0);
    if (now < end) {
      return isoDate(now);
    }
  }

  const start = new Date(now);
  start.setHours(12, 0, 0, 0);
  start.setDate(start.getDate() + 1);
  for (let offset = 0; offset < 21; offset += 1) {
    const candidate = new Date(start);
    candidate.setDate(start.getDate() + offset);
    if (schedules.some((row) => row.weekday === jsToPythonWeekday(candidate.getDay()))) {
      return isoDate(candidate);
    }
  }
  return null;
}

function setStatus(message, kind = "") {
  if (!els.status) return;
  els.status.textContent = message || "";
  els.status.className = "form-status" + (kind ? ` is-${kind}` : "");
}

function resetSlots(message) {
  state.selectedSlot = null;
  if (els.slots) {
    els.slots.innerHTML = `<p class="slots__empty">${escapeHtml(message)}</p>`;
  }
  updateSubmit();
}

function updateSubmit() {
  if (!els.submit) return;
  const ready = Boolean(
    state.token &&
      state.selectedSlot &&
      els.doctor.value &&
      els.date.value,
  );
  els.submit.disabled = !ready;
}

function renderDepartments(departments) {
  const list = document.getElementById("specialties-list");
  if (!list) return;

  if (!departments.length) {
    list.innerHTML = '<li class="specialties__empty">لا توجد تخصصات مضافة بعد.</li>';
    return;
  }

  list.innerHTML = departments
    .map(
      (department, index) => `
        <li>
          <span>${String(index + 1).padStart(2, "0")}</span>
          <span class="specialties__name">
            ${escapeHtml(department.name)}
            ${department.description ? `<small>${escapeHtml(department.description)}</small>` : ""}
          </span>
        </li>`,
    )
    .join("");
}

function monogram(name) {
  return String(name)
    .replace(/^(د\.?|Dr\.?)\s*/i, "")
    .trim()
    .charAt(0);
}

function renderDoctors(doctors, departments) {
  const grid = document.getElementById("doctors-grid");
  if (!grid) return;

  if (!doctors.length) {
    grid.innerHTML = '<p class="doctors__empty">لا يوجد أطباء متاحون حاليًا.</p>';
    return;
  }

  const departmentNames = new Map(departments.map((item) => [item.id, item.name]));

  grid.innerHTML = doctors
    .map((doctor) => {
      const department = departmentNames.get(doctor.department_id) || "تخصص عام";
      return `
        <article class="doctor-card">
          <div class="doctor-card__mono" aria-hidden="true">${escapeHtml(monogram(doctor.full_name))}</div>
          <div class="doctor-card__body">
            <p class="doctor-card__dept">${escapeHtml(department)}</p>
            <h3>${escapeHtml(doctor.full_name)}</h3>
            <p class="doctor-card__spec">${escapeHtml(doctor.specialization)}</p>
            ${doctor.bio ? `<p class="doctor-card__bio">${escapeHtml(doctor.bio)}</p>` : ""}
            <a class="text-link" href="#booking" data-book-doctor="${doctor.id}">احجز مع الدكتور <span>←</span></a>
          </div>
        </article>`;
    })
    .join("");
}

function fillDepartmentOptions(departments) {
  if (!els.department) return;
  els.department.innerHTML =
    '<option value="">كل التخصصات</option>' +
    departments
      .map(
        (department) =>
          `<option value="${department.id}">${escapeHtml(department.name)}</option>`,
      )
      .join("");
}

function fillDoctorOptions(departmentId = "") {
  if (!els.doctor) return;
  const doctors = departmentId
    ? state.doctors.filter((doctor) => doctor.department_id === Number(departmentId))
    : state.doctors;

  els.doctor.innerHTML =
    '<option value="">اختار الدكتور</option>' +
    doctors
      .map(
        (doctor) =>
          `<option value="${doctor.id}">${escapeHtml(doctor.full_name)} — ${escapeHtml(doctor.specialization)}</option>`,
      )
      .join("");
}

async function loadSlots() {
  state.selectedSlot = null;
  updateSubmit();

  const doctorId = Number(els.doctor.value);
  const date = els.date.value;

  if (!doctorId || !date) {
    resetSlots("اختار الدكتور واليوم الأول.");
    return;
  }

  els.slots.innerHTML = '<p class="slots__empty">جارٍ تحميل المواعيد…</p>';

  try {
    const slots = await getJSON(
      `/appointments/available?doctor_id=${doctorId}&appointment_date=${date}`,
    );
    if (!slots.length) {
      els.slots.innerHTML =
        '<p class="slots__empty">لا توجد مواعيد متاحة في هذا اليوم. جرّب يومًا آخر.</p>';
      return;
    }
    els.slots.innerHTML = slots
      .map(
        (slot) =>
          `<button type="button" class="slot" data-start="${slot.start_time}">${formatTime(slot.start_time)}</button>`,
      )
      .join("");
  } catch (error) {
    console.error(error);
    els.slots.innerHTML =
      '<p class="slots__empty">تعذّر تحميل المواعيد. حاول تحديث الصفحة.</p>';
  }
}

async function onDoctorChange() {
  state.selectedSlot = null;
  updateSubmit();
  els.days.textContent = "";
  els.date.value = "";
  resetSlots("اختار اليوم لعرض المواعيد.");

  const doctorId = Number(els.doctor.value);
  if (!doctorId) {
    return;
  }

  try {
    const schedules = await getJSON(`/doctors/${doctorId}/schedules/`);
    if (!schedules.length) {
      els.days.textContent = "لا توجد مواعيد عمل مضافة لهذا الدكتور.";
      return;
    }

    const names = [...new Set(schedules.map((row) => WEEKDAY_NAMES[row.weekday]))].join("، ");
    els.days.textContent = `أيام العمل: ${names}`;

    const nextDate = pickBookingDate(schedules);
    if (nextDate) {
      els.date.value = nextDate;
      await loadSlots();
    }
  } catch (error) {
    console.error(error);
    els.days.textContent = "تعذّر تحميل مواعيد عمل الدكتور.";
  }
}

function switchAuthTab(name) {
  els.auth.querySelectorAll("[data-auth-tab]").forEach((tab) => {
    tab.classList.toggle("is-active", tab.dataset.authTab === name);
  });
  els.auth.querySelectorAll("[data-auth-panel]").forEach((panel) => {
    panel.hidden = panel.dataset.authPanel !== name;
  });
}

function renderAuth() {
  if (!els.auth) return;

  if (state.user) {
    els.auth.innerHTML = `
      <div class="auth__user">
        <div>
          <strong>${escapeHtml(state.user.full_name)}</strong>
          <small>${escapeHtml(state.user.email)}</small>
        </div>
        <button type="button" class="auth__logout" id="logout">خروج</button>
      </div>`;
    return;
  }

  els.auth.innerHTML = `
    <div class="auth__tabs">
      <button type="button" class="auth__tab is-active" data-auth-tab="login">تسجيل الدخول</button>
      <button type="button" class="auth__tab" data-auth-tab="register">حساب جديد</button>
    </div>
    <div class="auth__panel" data-auth-panel="login">
      <p class="auth__note">سجّل دخولك عشان نأكد الحجز باسمك.</p>
      <label class="field">
        <span>الإيميل</span>
        <input type="email" id="login-email" autocomplete="email" dir="ltr">
      </label>
      <label class="field">
        <span>الباسورد</span>
        <input type="password" id="login-password" autocomplete="current-password" dir="ltr">
      </label>
      <button class="btn btn--ghost" type="button" id="login-submit">دخول</button>
    </div>
    <div class="auth__panel" data-auth-panel="register" hidden>
      <p class="auth__note">حساب جديد بياخد ثواني.</p>
      <label class="field">
        <span>الاسم الكامل</span>
        <input type="text" id="register-name" autocomplete="name">
      </label>
      <label class="field">
        <span>الإيميل</span>
        <input type="email" id="register-email" autocomplete="email" dir="ltr">
      </label>
      <label class="field">
        <span>الباسورد (8 حروف على الأقل)</span>
        <input type="password" id="register-password" autocomplete="new-password" dir="ltr">
      </label>
      <button class="btn btn--gold" type="button" id="register-submit">إنشاء الحساب</button>
    </div>`;
}

function clearSession() {
  state.token = null;
  state.user = null;
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}

async function startSession(token) {
  state.token = token;
  localStorage.setItem(TOKEN_KEY, token);
  try {
    const me = await api("/auth/me");
    state.user = me;
    localStorage.setItem(USER_KEY, JSON.stringify(me));
  } catch (error) {
    clearSession();
    throw error;
  }
  renderAuth();
  updateSubmit();
}

async function requestToken(email, password) {
  const response = await fetch("/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({ username: email, password }),
  });
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    const error = new Error(detailOf(data) || "تعذّر تسجيل الدخول");
    error.status = response.status;
    throw error;
  }
  return data.access_token;
}

async function handleLogin() {
  const email = document.getElementById("login-email").value.trim();
  const password = document.getElementById("login-password").value;

  if (!email || !password) {
    setStatus("اكتب الإيميل والباسورد.", "error");
    return;
  }

  setStatus("جارٍ تسجيل الدخول…");

  try {
    const token = await requestToken(email, password);
    await startSession(token);
    setStatus("تم تسجيل الدخول. اختار ميعاد وأكد الحجز.", "ok");
  } catch (error) {
    setStatus(
      error.status === 401 ? "الإيميل أو الباسورد غلط." : error.message,
      "error",
    );
  }
}

async function handleRegister() {
  const fullName = document.getElementById("register-name").value.trim();
  const email = document.getElementById("register-email").value.trim();
  const password = document.getElementById("register-password").value;

  if (fullName.length < 2) {
    setStatus("اكتب اسمك الكامل.", "error");
    return;
  }
  if (!email) {
    setStatus("اكتب الإيميل.", "error");
    return;
  }
  if (password.length < 8) {
    setStatus("الباسورد لازم 8 حروف على الأقل.", "error");
    return;
  }

  setStatus("جارٍ إنشاء الحساب…");

  try {
    const response = await fetch("/auth/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        full_name: fullName,
        email,
        password,
      }),
    });
    const data = await response.json().catch(() => null);
    if (!response.ok) {
      const error = new Error(detailOf(data) || "تعذّر إنشاء الحساب");
      error.status = response.status;
      throw error;
    }

    const token = await requestToken(email, password);
    await startSession(token);
    setStatus("تم إنشاء الحساب وتسجيل الدخول.", "ok");
  } catch (error) {
    if (error.status === 400) {
      setStatus("الإيميل ده مسجل قبل كده. جرّب تسجيل الدخول.", "error");
    } else {
      setStatus(error.message, "error");
    }
  }
}

function handleLogout() {
  clearSession();
  renderAuth();
  updateSubmit();
  setStatus("تم تسجيل الخروج.");
}

function showSuccess(appointment, doctor) {
  const doctorName = doctor ? doctor.full_name : "الطبيب";
  els.successText.textContent = `${doctorName} — ${formatDate(appointment.appointment_date)}، الساعة ${formatTime(appointment.start_time)}`;
  els.form.hidden = true;
  els.success.hidden = false;
  setStatus("");
  els.success.scrollIntoView({ behavior: "smooth", block: "center" });
}

function resetBookingForm() {
  els.form.hidden = false;
  els.success.hidden = true;
  els.notes.value = "";
  state.selectedSlot = null;
  els.date.value = "";
  resetSlots("اختار الدكتور واليوم الأول.");
  setStatus("");
  if (els.doctor.value) {
    onDoctorChange();
  } else {
    updateSubmit();
  }
}

function openModal() {
  els.modal.hidden = false;
  document.body.style.overflow = "hidden";
}

function closeModal() {
  els.modal.hidden = true;
  document.body.style.overflow = "";
}

async function openAppointments() {
  openModal();

  if (!state.token) {
    els.appointmentsList.innerHTML =
      '<p class="modal__empty">سجّل الدخول الأول عشان تشوف حجوزاتك.</p>';
    return;
  }

  els.appointmentsList.innerHTML = '<p class="modal__empty">جارٍ التحميل…</p>';

  try {
    const appointments = await api("/appointments/my");
    if (!appointments.length) {
      els.appointmentsList.innerHTML =
        '<p class="modal__empty">مفيش حجوزات لسه. احجز ميعادك الأول.</p>';
      return;
    }

    els.appointmentsList.innerHTML = appointments
      .map((appointment) => {
        const doctor = state.doctors.find((item) => item.id === appointment.doctor_id);
        const statusLabel = STATUS_LABELS[appointment.status] || appointment.status;
        return `
          <div class="appointment">
            <div>
              <strong>${escapeHtml(doctor ? doctor.full_name : "طبيب")}</strong>
              <small>${formatDate(appointment.appointment_date)} — ${formatTime(appointment.start_time)}</small>
            </div>
            <div class="appointment__meta">
              <span class="appointment__status is-${escapeHtml(appointment.status)}">${escapeHtml(statusLabel)}</span>
              ${
                appointment.status === "confirmed"
                  ? `<br><button type="button" class="appointment__cancel" data-cancel-id="${appointment.id}">إلغاء الحجز</button>`
                  : ""
              }
            </div>
          </div>`;
      })
      .join("");
  } catch (error) {
    console.error(error);
    els.appointmentsList.innerHTML =
      '<p class="modal__empty">تعذّر تحميل الحجوزات. حدّث الصفحة وحاول تاني.</p>';
  }
}

async function cancelAppointment(id) {
  try {
    await api(`/appointments/${id}/cancel`, { method: "POST" });
    setStatus("تم إلغاء الحجز.", "ok");
    await openAppointments();
    await loadSlots();
  } catch (error) {
    setStatus(error.message || "تعذّر إلغاء الحجز.", "error");
  }
}

async function restoreSession() {
  if (!state.token) return;
  try {
    const me = await api("/auth/me");
    state.user = me;
    localStorage.setItem(USER_KEY, JSON.stringify(me));
  } catch {
    clearSession();
  }
}

async function loadContent() {
  try {
    const [departments, doctors] = await Promise.all([
      getJSON("/departments/"),
      getJSON("/doctors/"),
    ]);
    state.departments = departments;
    state.doctors = doctors;
    renderDepartments(departments);
    renderDoctors(doctors, departments);
    fillDepartmentOptions(departments);
    fillDoctorOptions();
  } catch (error) {
    console.error(error);
    const grid = document.getElementById("doctors-grid");
    if (grid) {
      grid.innerHTML =
        '<p class="doctors__empty">تعذّر تحميل البيانات. حدّث الصفحة للمحاولة مرة أخرى.</p>';
    }
  }
}

function setupBookingEvents() {
  els.date.min = isoDate(new Date());

  els.department.addEventListener("change", () => {
    fillDoctorOptions(els.department.value);
    els.doctor.value = "";
    els.date.value = "";
    els.days.textContent = "";
    resetSlots("اختار الدكتور واليوم الأول.");
  });

  els.doctor.addEventListener("change", onDoctorChange);
  els.date.addEventListener("change", loadSlots);

  els.slots.addEventListener("click", (event) => {
    const button = event.target.closest(".slot");
    if (!button) return;
    state.selectedSlot = button.dataset.start;
    els.slots.querySelectorAll(".slot").forEach((item) => {
      item.classList.toggle("is-selected", item === button);
    });
    updateSubmit();
  });

  els.auth.addEventListener("click", (event) => {
    const tab = event.target.closest("[data-auth-tab]");
    if (tab) {
      switchAuthTab(tab.dataset.authTab);
      return;
    }
    if (event.target.id === "login-submit") {
      handleLogin();
    } else if (event.target.id === "register-submit") {
      handleRegister();
    } else if (event.target.id === "logout") {
      handleLogout();
    }
  });

  els.form.addEventListener("submit", async (event) => {
    event.preventDefault();

    if (!state.token) {
      setStatus("سجّل الدخول الأول عشان نأكد الحجز.", "error");
      return;
    }
    if (!state.selectedSlot) {
      setStatus("اختار ميعاد من المتاح.", "error");
      return;
    }

    const doctorId = Number(els.doctor.value);
    const doctor = state.doctors.find((item) => item.id === doctorId);

    els.submit.disabled = true;
    setStatus("جارٍ تأكيد الحجز…");

    try {
      const appointment = await api("/appointments/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          doctor_id: doctorId,
          appointment_date: els.date.value,
          start_time: state.selectedSlot,
          notes: els.notes.value.trim() || null,
        }),
      });
      showSuccess(appointment, doctor);
      await loadSlots();
    } catch (error) {
      if (error.status === 409) {
        setStatus("الميعاد اتحجز للتو. اختار ميعاد تاني.", "error");
        await loadSlots();
      } else if (error.status === 401) {
        clearSession();
        renderAuth();
        setStatus("انتهت الجلسة. سجّل الدخول تاني.", "error");
      } else {
        setStatus(error.message || "تعذّر تأكيد الحجز. حاول تاني.", "error");
      }
    } finally {
      updateSubmit();
    }
  });

  document.addEventListener("click", (event) => {
    const link = event.target.closest("[data-book-doctor]");
    if (!link) return;
    event.preventDefault();

    const doctorId = Number(link.dataset.bookDoctor);
    if (!state.doctors.some((doctor) => doctor.id === doctorId)) return;

    els.department.value = "";
    fillDoctorOptions();
    els.doctor.value = String(doctorId);
    onDoctorChange();
    document.getElementById("booking").scrollIntoView({ behavior: "smooth", block: "start" });
  });

  els.modal.addEventListener("click", (event) => {
    if (event.target.closest("[data-close-modal]")) {
      closeModal();
    }
  });

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && !els.modal.hidden) {
      closeModal();
    }
  });

  els.appointmentsList.addEventListener("click", (event) => {
    const button = event.target.closest("[data-cancel-id]");
    if (!button) return;
    cancelAppointment(Number(button.dataset.cancelId));
  });

  document.getElementById("view-appointments").addEventListener("click", openAppointments);
  document.getElementById("book-another").addEventListener("click", resetBookingForm);
}

async function init() {
  setupBookingEvents();
  await loadContent();
  await restoreSession();
  renderAuth();
  updateSubmit();
}

init();
