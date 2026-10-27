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

const escapeHtml = (value) =>
  String(value).replace(/[&<>"']/g, (ch) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;",
  }[ch]));

async function getJSON(url) {
  const response = await fetch(url, { headers: { Accept: "application/json" } });
  if (!response.ok) {
    throw new Error(`${url} -> ${response.status}`);
  }
  return response.json();
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

function initials(name) {
  return String(name)
    .replace(/\b(Dr|د)\.?\s*/gi, "")
    .trim()
    .split(/\s+/)
    .slice(0, 2)
    .map((part) => part.charAt(0))
    .join("")
    .toUpperCase();
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
          <div class="doctor-card__mono" aria-hidden="true">${escapeHtml(initials(doctor.full_name))}</div>
          <div class="doctor-card__body">
            <p class="doctor-card__dept">${escapeHtml(department)}</p>
            <h3>${escapeHtml(doctor.full_name)}</h3>
            <p class="doctor-card__spec">${escapeHtml(doctor.specialization)}</p>
            ${doctor.bio ? `<p class="doctor-card__bio">${escapeHtml(doctor.bio)}</p>` : ""}
            <a class="text-link" href="#contact">احجز مع الدكتور <span>←</span></a>
          </div>
        </article>`;
    })
    .join("");
}

async function loadContent() {
  try {
    const [departments, doctors] = await Promise.all([
      getJSON("/departments/"),
      getJSON("/doctors/"),
    ]);
    renderDepartments(departments);
    renderDoctors(doctors, departments);
  } catch (error) {
    console.error(error);
    const grid = document.getElementById("doctors-grid");
    if (grid) {
      grid.innerHTML =
        '<p class="doctors__empty">تعذّر تحميل البيانات. حدّث الصفحة للمحاولة مرة أخرى.</p>';
    }
  }
}

loadContent();
