let reservaAEliminar = null;

document.addEventListener("DOMContentLoaded", async () => {
  // --- VARIABLES GLOBALES PARA MODALES ---
  let pseModal, cardModal, successModal, reservationToast, loginRegisterModal;

  // --- 1. LÓGICA DE CARGA DE COMPONENTES ---
  async function cargarComponente(id, url) {
    const contenedor = document.getElementById(id);

    if (!contenedor) return;

    try {
      if (
        url.includes("iniciarsesion.html") ||
        url.includes("registrarse.html") ||
        url.includes("agenda.html")
      ) {
        window.location.href = url;
        return;
      }

      const response = await fetch(url);

      if (!response.ok) {
        throw new Error("No se pudo cargar");
      }

      contenedor.innerHTML = await response.text();

      // ← NUEVO
      if (id === "navbar-container") {
        inicializarNavbar();
      }

      if (id === "main-content") {
        if (url.includes("info.html")) {
          activarNav("nav-inicio");
          activarDetectorSecciones();
          iniciarCarruselVisual();
        }

        if (url.includes("reservas.html")) {
          activarNav("nav-agendar");

          setTimeout(() => {
            if (document.getElementById("calendarDays")) {
              inicializarLogicaReserva();
            }
          }, 150);
        }

        if (document.querySelector(".barbers-track")) {
          inicializarCarousel();
        }
      }
    } catch (err) {
      console.error("Error cargando componente:", err);
    }
  }

  // Cargas iniciales
  if (document.getElementById("navbar-container")) {
    await cargarComponente(
      "navbar-container",
      `${rutaBase}/componentes/navbar.html`,
    );
  }

  if (document.getElementById("footer-container")) {
    cargarComponente("footer-container", `${rutaBase}/componentes/footer.html`);
  }

  if (false && document.getElementById("main-content")) {
    cargarComponente("main-content", `${rutaBase}/secciones/info.html`);
  }

  const urlParams = new URLSearchParams(window.location.search);
  if (
    urlParams.get("reserva") === "true" &&
    JSON.parse(localStorage.getItem("sesionActiva"))
  ) {
    activarNav("nav-agendar");
    cargarComponente("main-content", `${rutaBase}/secciones/reservas.html`);
  }

  console.log("Existe formReservas:", document.getElementById("formReservas"));

  if (document.getElementById("formReservas")) {
    console.log("Voy a inicializar reservas");
    inicializarLogicaReserva();
  }

  if (document.getElementById("loginRegisterModal")) {
    loginRegisterModal = new bootstrap.Modal(
      document.getElementById("loginRegisterModal"),
    );

    const loginTabButton = document.getElementById("login-tab");
    const registerTabButton = document.getElementById("register-tab");
    const switchToRegisterBtn = document.getElementById("switchToRegisterBtn");
    const switchToLoginBtn = document.getElementById("switchToLoginBtn");

    if (switchToRegisterBtn && registerTabButton) {
      switchToRegisterBtn.addEventListener("click", () =>
        new bootstrap.Tab(registerTabButton).show(),
      );
    }

    if (switchToLoginBtn && loginTabButton) {
      switchToLoginBtn.addEventListener("click", () =>
        new bootstrap.Tab(loginTabButton).show(),
      );
    }

    console.log("¿Existe formReservas?", document.getElementById("formReservas"));

    if (document.getElementById("formReservas")) {
    inicializarLogicaReserva();
    }
  }

  function mostrarAuthModal() {
    const sesion = JSON.parse(localStorage.getItem("sesionActiva"));

    if (sesion) {
      activarNav("nav-agendar");
      cargarComponente("main-content", `${rutaBase}/secciones/reservas.html`);
      return;
    }

    sessionStorage.setItem("loginAfterReserve", "true");

    if (loginRegisterModal) {
      loginRegisterModal.show();
      return;
    }

    window.location.href = `${rutaBase}/secciones/iniciarsesion.html`;
  }

  document.addEventListener("click", (event) => {
    const reservaBtn = event.target.closest(".btn-servicio-reservar");
    if (!reservaBtn) return;

    event.preventDefault();

    const sesion = JSON.parse(localStorage.getItem("sesionActiva"));

    if (sesion) {
      activarNav("nav-agendar");
      cargarComponente("main-content", `${rutaBase}/secciones/reservas.html`);
    } else {
      mostrarAuthModal();
    }
  });

  // --- 2. GESTIÓN DE RESERVA ---
  window.gestionarReserva = function (event) {
    event.preventDefault();

    const sesion = JSON.parse(localStorage.getItem("sesionActiva"));

    if (sesion) {
      activarNav("nav-agendar");

      cargarComponente("main-content", `${rutaBase}/secciones/reservas.html`);
    } else {
      window.location.href = `${rutaBase}/secciones/agenda.html`;
    }
  };

  // --- 3. LÓGICA DE RESERVA ---
  function inicializarLogicaReserva() {
    console.log("ENTRÓ A inicializarLogicaReserva");
    const required = [
      "servicio",
      "barbero",
      "calendarDays",
      "hoursGrid",
      "btnReservar"
    ];

    if (required.some(id => !document.getElementById(id))) {
      console.warn("Reserva module: DOM incompleto, reintentando...");
      setTimeout(inicializarLogicaReserva, 200);
      return;
    }

    if (!pseModal) {
      pseModal = new bootstrap.Modal(document.getElementById("pseModal"));
      cardModal = new bootstrap.Modal(document.getElementById("cardModal"));
      successModal = new bootstrap.Modal(
        document.getElementById("successModal"),
      );
      reservationToast = new bootstrap.Toast(
        document.getElementById("reservationToast"),
        { delay: 3000 },
      );
    }

    console.log("Lógica de reserva inicializada");
    inicializarModuloReservas();

    document
    .getElementById("confirmarCancelarReserva")
    ?.addEventListener("click",()=>{

        const modal =
            bootstrap.Modal.getInstance(
                document.getElementById("cancelReservationModal")
            );

        modal.hide();

        cancelarReserva(reservaAEliminar);

    });
  }

  // --- 4. LOGIN Y REGISTRO ---

  // Helpers para manejo de múltiples usuarios en localStorage
  function obtenerUsuarios() {
    return JSON.parse(localStorage.getItem("usuarios")) || [];
  }

  function guardarUsuarios(usuarios) {
    localStorage.setItem("usuarios", JSON.stringify(usuarios));
  }

  function encontrarUsuarioPorEmail(email) {
    const usuarios = obtenerUsuarios();
    return usuarios.find((u) => u.email === email || u.correo === email);
  }

  function actualizarUsuarioEnAlmacen(usuarioActualizado) {
    const usuarios = obtenerUsuarios();
    const idx = usuarios.findIndex(
      (u) =>
        (u.email || u.correo) ===
        (usuarioActualizado.email || usuarioActualizado.correo),
    );
    if (idx !== -1) {
      usuarios[idx] = { ...usuarios[idx], ...usuarioActualizado };
      guardarUsuarios(usuarios);
    } else {
      // si no existe, agregar
      usuarios.push(usuarioActualizado);
      guardarUsuarios(usuarios);
    }
  }

  const formRegistro = document.getElementById("registro-form");
  if (formRegistro) {
    formRegistro.addEventListener("submit", (e) => {
      e.preventDefault();

      const nombreInput =
        document.getElementById("nombre") ||
        document.getElementById("modal-registro-nombre");
      const apellidoInput =
        document.getElementById("apellido") ||
        document.getElementById("modal-registro-apellido");
      const emailInput =
        document.getElementById("correo") ||
        document.getElementById("modal-registro-correo");
      const passwordInput =
        document.getElementById("modal-registro-password") ||
        document.getElementById("password");

      // Validar confirmación de contraseña si existe
      const confirmarPasswordInput =
        document.getElementById("confirmar-password");
      if (
        confirmarPasswordInput &&
        confirmarPasswordInput.value &&
        passwordInput &&
        confirmarPasswordInput.value !== passwordInput.value
      ) {
        alert("Las contraseñas no coinciden.");
        return;
      }

      const nuevoUsuario = {
        nombre: nombreInput?.value || "",
        apellido: apellidoInput?.value || "",
        email: (emailInput?.value || "").toLowerCase(),
        password: passwordInput?.value || "",
        telefono:
          (
            document.getElementById("telefono") ||
            document.getElementById("modal-registro-telefono")
          )?.value || "",
        allowBirthdayEditOnce: true,
      };

      // Si el formulario de registro incluye un input de tipo date (secciones/registrarse.html), guardar la fecha
      const fechaInput =
        document.getElementById("fecha") ||
        document.getElementById("modal-registro-fecha");
      if (fechaInput && fechaInput.value) {
        const parts = fechaInput.value.split("-"); // yyyy-mm-dd
        if (parts.length === 3) {
          nuevoUsuario.anioNac = parts[0];
          nuevoUsuario.mesNac = parts[1];
          nuevoUsuario.diaNac = parts[2];
          // Si el usuario se registra desde la página completa, no podrá editar su fecha en el perfil
          nuevoUsuario.allowBirthdayEditOnce = false;
        }
      }

      const usuarios = obtenerUsuarios();
      if (usuarios.some((u) => (u.email || u.correo) === nuevoUsuario.email)) {
        alert("Ya existe un usuario con ese correo. Por favor inicia sesión.");
        if (loginRegisterModal) {
          const loginTabButton = document.getElementById("login-tab");
          if (loginTabButton) new bootstrap.Tab(loginTabButton).show();
        }
        return;
      }

      usuarios.push(nuevoUsuario);
      guardarUsuarios(usuarios);

      // Marcar como usuario nuevo para redirigir a perfil después de login
      sessionStorage.setItem("newUserAfterRegister", "true");

      if (loginRegisterModal) {
        const loginTabButton = document.getElementById("login-tab");
        if (loginTabButton) new bootstrap.Tab(loginTabButton).show();
        return;
      }

      window.location.href = `${rutaBase}/secciones/iniciarsesion.html`;
    });
  }

  const formLogin = document.getElementById("form-login");
  if (formLogin) {
    formLogin.addEventListener("submit", (e) => {
      e.preventDefault();

      const inputUsuario = (
        document.getElementById("usuario").value || ""
      ).toLowerCase();
      const inputPass = document.getElementById("password").value;

      const usuarios = obtenerUsuarios();
      const encontrado = usuarios.find(
        (u) =>
          ((u.email || u.correo) === inputUsuario ||
            (u.telefono || "") === inputUsuario) &&
          u.password === inputPass,
      );

      if (encontrado) {
        localStorage.setItem("sesionActiva", JSON.stringify(encontrado));

        // Si usuario nuevo se registró y ahora inicia sesión, redirigir a perfil
        if (sessionStorage.getItem("newUserAfterRegister") === "true") {
          sessionStorage.removeItem("newUserAfterRegister");

          // Guardar la cita pendiente para procesarla después de completar el perfil
          if (sessionStorage.getItem("afterAgendaReserve")) {
            sessionStorage.setItem(
              "reservaAfterPerfil",
              sessionStorage.getItem("afterAgendaReserve"),
            );
            sessionStorage.removeItem("afterAgendaReserve");
          }

          if (loginRegisterModal) {
            loginRegisterModal.hide();
          }

          activarNav("nav-agendar");
          cargarComponente("main-content", `${rutaBase}/secciones/perfil.html`);
          inicializarLogicaPerfil();
          return;
        }

        // Si venimos de intentar reservar desde un servicio
        if (sessionStorage.getItem("loginAfterReserve") === "true") {
          sessionStorage.removeItem("loginAfterReserve");

          if (loginRegisterModal) {
            loginRegisterModal.hide();
            activarNav("nav-agendar");
            cargarComponente(
              "main-content",
              `${rutaBase}/secciones/reservas.html`,
            );
            return;
          }

          window.location.href = `${rutaBase}/index.html?reserva=true`;
          return;
        }

        // Si venimos desde el formulario de agenda que mostró el modal de auth
        if (sessionStorage.getItem("afterAgendaReserve")) {
          try {
            const reservaPendiente = JSON.parse(
              sessionStorage.getItem("afterAgendaReserve"),
            );
            sessionStorage.removeItem("afterAgendaReserve");

            if (typeof guardarReserva === "function") {
              guardarReserva(reservaPendiente);
            }

            // Mostrar confirmación si existe el toast, si no usar alert
            const toastEl = document.getElementById("reservationToast");
            if (toastEl && bootstrap && bootstrap.Toast) {
              const t = new bootstrap.Toast(toastEl);
              t.show();
            } else {
              alert("Reserva registrada exitosamente.");
            }

            // Asegurar que las notificaciones se actualicen
            if (typeof actualizarNotificaciones === "function")
              actualizarNotificaciones();

            if (loginRegisterModal) {
              loginRegisterModal.hide();
            }

            // Redirigir a inicio donde el navbar mostrará la campana actualizada
            window.location.href = `${rutaBase}/index.html`;
            return;
          } catch (err) {
            console.error("Error procesando reserva pendiente:", err);
          }
        }

        if (loginRegisterModal) {
          loginRegisterModal.hide();
        }

        window.location.href = `${rutaBase}/index.html`;
      } else {
        alert("Usuario o contraseña incorrectos");
      }
    });
  }
});

// --- FUNCIONES GLOBALES ---
function inicializarNavbar() {
  const sesion = JSON.parse(localStorage.getItem("sesionActiva"));
  const authLinks = document.getElementById("auth-links");
  const dynamicArea = document.getElementById("dynamic-nav-area");
  const mobileBell = document.getElementById("mobile-bell-container");
  const mobileExtra = document.getElementById("mobile-extra-options");
  const logoContainer = document.getElementById("logo-container");
  const gearIcon = document.getElementById("gear-icon-desktop");
  const brandRole = document.getElementById("brand-role"); // Capturamos el elemento

  if (dynamicArea) dynamicArea.innerHTML = "";
  if (mobileBell) mobileBell.innerHTML = "";
  if (mobileExtra) mobileExtra.innerHTML = "";

  const campanaHTML = `
        <div id="bell-wrapper" style="position: relative;">
            <i id="btn-notificaciones" class="bi bi-bell-fill text-warning" style="font-size: 1.2rem; cursor: pointer;"></i>
            <div id="notificaciones-panel">
                <h6 class="border-bottom border-warning pb-2">Notificaciones</h6>
                <div id="lista-notificaciones">No tienes notificaciones nuevas.</div>
            </div>
        </div>
    `;

  const agregarEventoCampana = () => {
    const btn = document.getElementById("btn-notificaciones");
    const panel = document.getElementById("notificaciones-panel");
    if (btn && panel) {
      btn.onclick = (e) => {
        e.stopPropagation();
        panel.classList.toggle("active");
      };
    }
  };

  document.addEventListener("click", (e) => {
    const panel = document.getElementById("notificaciones-panel");
    const btn = document.getElementById("btn-notificaciones");
    if (panel && panel.classList.contains("active") && e.target !== btn) {
      panel.classList.remove("active");
    }
  });

  if (sesion) {
    // --- LÓGICA CON SESIÓN ---
    if (brandRole) brandRole.style.display = "block"; // Mostrar rol
    if (authLinks) authLinks.classList.add("d-none");
    if (!document.getElementById("side-menu")) crearSideMenuDOM(sesion);

    if (window.innerWidth >= 992) {
      if (gearIcon) {
        gearIcon.classList.remove("d-none");
        gearIcon.style.setProperty("display", "inline-block", "important");
        gearIcon.onclick = (e) => toggleSideMenu(e);
      }
      if (logoContainer)
        logoContainer.style.setProperty("display", "none", "important");
      if (dynamicArea) {
        dynamicArea.innerHTML = `<span class="text-warning fw-bold px-3">Hola, ${sesion.nombre}</span> ${campanaHTML}`;
        agregarEventoCampana();
        actualizarNotificaciones();
      }
    } else {
      if (logoContainer)
        logoContainer.style.setProperty("display", "flex", "important");
      if (mobileBell) {
        mobileBell.innerHTML = campanaHTML;
        agregarEventoCampana();
        actualizarNotificaciones();
      }
      if (gearIcon) gearIcon.style.setProperty("display", "none", "important");

      if (mobileExtra) {
        mobileExtra.innerHTML = `
                    <hr class="text-white">
                    <li class="nav-item">
                        <a class="nav-link" id="nav-perfil" href="#" onclick="window.cargarSeccion('perfil.html'); activarNav('nav-perfil'); return false;">
                            👤 Mi Perfil
                        </a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" id="nav-mis-reservas" href="#" onclick="mostrarMisReservas(); return false;">
                            📅 Mis Reservas
                        </a>
                    </li>
                    <li class="nav-item">
                        <button onclick="cerrarSesion()" class="nav-link text-danger border-0 bg-transparent w-100">
                            Cerrar Sesión
                        </button>
                    </li>
                `;
      }
    }
  } else {
    // --- LÓGICA SIN SESIÓN ---
    if (brandRole) brandRole.style.display = "none"; // Ocultar rol
    if (authLinks) authLinks.classList.remove("d-none");
    if (logoContainer)
      logoContainer.style.setProperty("display", "flex", "important");
    if (gearIcon) gearIcon.style.setProperty("display", "none", "important");
  }
}

window.addEventListener("resize", inicializarNavbar);

function crearSideMenuDOM(sesion) {
  if (document.getElementById("side-menu")) return;

  const menu = document.createElement("div");
  menu.id = "side-menu";

  menu.innerHTML = `
        <span class="close-menu-btn" onclick="toggleSideMenu(event)">×</span>

        <div class="menu-header">
            <img src="${rutaBase}/img/logo.jpeg"
                 style="width: 80px;
                        height: 80px;
                        border-radius: 50%;
                        border: 2px solid #FFC600;">

            <h5 class="text-white mt-3">${sesion.nombre}</h5>
        </div>

        <div class="menu-items">

            <a href="#"
               onclick="
                   window.cargarSeccion('perfil.html');
                   toggleSideMenu(event);
                   return false;
               ">
                👤 Mi Perfil
            </a>

            <a href="#"
              onclick="
                  mostrarMisReservas();
                  toggleSideMenu(event);
                  return false;
              ">
                📅 Mis Reservas
            </a>

            <button onclick="cerrarSesion()"
                    class="btn btn-outline-danger w-100 mt-4">
                Cerrar Sesión
            </button>

        </div>
    `;

  const overlay = document.createElement("div");
  overlay.id = "menu-overlay";
  overlay.onclick = toggleSideMenu;

  document.body.appendChild(menu);
  document.body.appendChild(overlay);
}

function toggleSideMenu(e) {
  if (e) {
    e.preventDefault();
    e.stopPropagation();
  }
  const menu = document.getElementById("side-menu");
  const overlay = document.getElementById("menu-overlay");
  if (menu && overlay) {
    const isActive = menu.classList.toggle("active");
    overlay.style.display = isActive ? "block" : "none";
    document.body.style.overflow = isActive ? "hidden" : "";
  }
}

function inicializarCarousel() {
  const track = document.querySelector(".barbers-track");
  const nextBtn = document.getElementById("nextBtn");
  const prevBtn = document.getElementById("prevBtn");

  if (!track || !nextBtn || !prevBtn) return;

  let isAnimating = false; // 🔒 CONTROL DE BLOQUEO

  const getScrollAmount = () => {
    const firstCard = track.querySelector(".barber-card");
    return firstCard ? firstCard.offsetWidth + 24 : 300;
  };

  nextBtn.addEventListener("click", () => {
    if (isAnimating) return; // 🚫 evita spam clicks
    isAnimating = true;

    const cardWidth = getScrollAmount();

    track.style.transition = "transform 0.5s ease-in-out";
    track.style.transform = `translateX(-${cardWidth}px)`;

    track.addEventListener(
      "transitionend",
      () => {
        track.style.transition = "none";
        track.appendChild(track.firstElementChild);
        track.style.transform = "translateX(0)";

        isAnimating = false; // 🔓 desbloquea
      },
      { once: true },
    );
  });

  prevBtn.addEventListener("click", () => {
    if (isAnimating) return; // 🚫 evita spam clicks
    isAnimating = true;

    const cardWidth = getScrollAmount();

    track.insertBefore(track.lastElementChild, track.firstElementChild);

    track.style.transition = "none";
    track.style.transform = `translateX(-${cardWidth}px)`;

    track.offsetHeight; // fuerza reflow

    track.style.transition = "transform 0.5s ease-in-out";
    track.style.transform = "translateX(0)";

    track.addEventListener(
      "transitionend",
      () => {
        isAnimating = false; // 🔓 desbloquea
      },
      { once: true },
    );
  });
}

function cerrarSesion() {
  localStorage.removeItem("sesionActiva");
  alert("Has cerrado sesión.");
  window.location.href = `${rutaBase}/index.html`;
}

function inicializarLogicaPerfil() {
  const form = document.getElementById("formEditarPerfil");
  const sesion = JSON.parse(localStorage.getItem("sesionActiva"));
  const selectMes = document.getElementById("selectMes");
  const selectDia = document.getElementById("selectDia");
  const selectAnio = document.getElementById("selectAnio");

  if (!sesion || !form || !selectMes || !selectDia || !selectAnio) return;

  const meses = [
    "Enero",
    "Febrero",
    "Marzo",
    "Abril",
    "Mayo",
    "Junio",
    "Julio",
    "Agosto",
    "Septiembre",
    "Octubre",
    "Noviembre",
    "Diciembre",
  ];

  const actualizarDias = () => {
    const mesIndex = meses.indexOf(selectMes.value);
    const anio = parseInt(selectAnio.value, 10) || new Date().getFullYear();
    const diasEnMes = new Date(anio, mesIndex + 1, 0).getDate();
    const diaActual = parseInt(selectDia.value, 10);

    selectDia.innerHTML = "";
    for (let i = 1; i <= diasEnMes; i++) {
      const option = document.createElement("option");
      option.value = i;
      option.textContent = i;
      selectDia.appendChild(option);
    }

    if (diaActual && diaActual <= diasEnMes) {
      selectDia.value = diaActual;
    }
  };

  const llenarAnios = () => {
    const actual = new Date().getFullYear();
    selectAnio.innerHTML = "";
    for (let año = actual; año >= 1900; año--) {
      const option = document.createElement("option");
      option.value = año;
      option.textContent = año;
      selectAnio.appendChild(option);
    }
  };

  llenarAnios();
  actualizarDias();
  selectMes.addEventListener("change", actualizarDias);
  selectAnio.addEventListener("change", actualizarDias);

  // 1. Rellenar campos con los datos almacenados
  // Usamos || '' para evitar que se muestre "undefined" si el dato no existe
  document.getElementById("inputNombre").value = sesion.nombre || "";
  document.getElementById("inputTelefono").value = sesion.telefono || "";
  document.getElementById("inputPasswordActual").value = "";
  document.getElementById("inputPasswordNueva").value = "";

  // Seleccionar opciones en los <select>
  if (sesion.genero)
    document.getElementById("selectGenero").value = sesion.genero;
  if (sesion.mesNac) selectMes.value = sesion.mesNac;
  if (sesion.anioNac) selectAnio.value = sesion.anioNac;
  actualizarDias();
  if (sesion.diaNac) selectDia.value = sesion.diaNac;

  // Marcar los checkboxes
  document.getElementById("checkPromociones").checked = !!sesion.promoWpp;
  document.getElementById("checkCitas").checked = !!sesion.citasWpp;

  // Habilitar edición de nacimiento solo para nuevo usuario desde agenda una vez
  const puedeEditarNacimiento = !!sesion.allowBirthdayEditOnce;
  const birthFields = [selectMes, selectDia, selectAnio];
  birthFields.forEach((field) => {
    field.disabled = !puedeEditarNacimiento;
    if (field.disabled) {
      field.classList.add("disabled-input");
    } else {
      field.classList.remove("disabled-input");
    }
  });

  // 2. Escuchar el evento de envío del formulario
  form.addEventListener("submit", (e) => {
    e.preventDefault();

    // Actualizar el objeto sesion con los valores actuales del formulario
    sesion.nombre = document.getElementById("inputNombre").value;
    sesion.telefono = document.getElementById("inputTelefono").value;
    const passwordActual = document
      .getElementById("inputPasswordActual")
      .value.trim();
    const passwordNueva = document
      .getElementById("inputPasswordNueva")
      .value.trim();
    if (passwordNueva) {
      if (!passwordActual) {
        alert("Debes ingresar tu contraseña actual para cambiarla.");
        return;
      }
      if (passwordActual !== sesion.password) {
        alert("La contraseña actual no coincide.");
        return;
      }
      sesion.password = passwordNueva;
    }
    sesion.genero = document.getElementById("selectGenero").value;
    sesion.promoWpp = document.getElementById("checkPromociones").checked;
    sesion.citasWpp = document.getElementById("checkCitas").checked;

    const selectMes = document.getElementById("selectMes");
    const selectDia = document.getElementById("selectDia");
    const selectAnio = document.getElementById("selectAnio");
    const puedeEditarNacimiento = !!sesion.allowBirthdayEditOnce;

    if (puedeEditarNacimiento) {
      const mesNac = selectMes.value;
      const diaNac = selectDia.value;
      const anioNac = selectAnio.value;
      if (mesNac && diaNac && anioNac) {
        sesion.mesNac = mesNac;
        sesion.diaNac = diaNac;
        sesion.anioNac = anioNac;
        sesion.allowBirthdayEditOnce = false;
      }
    }

    localStorage.setItem("sesionActiva", JSON.stringify(sesion));
    actualizarUsuarioEnAlmacen(sesion);

    // Si hay una reserva pendiente después de completar el perfil, guardarla ahora
    if (sessionStorage.getItem("reservaAfterPerfil")) {
      try {
        const reservaPendiente = JSON.parse(
          sessionStorage.getItem("reservaAfterPerfil"),
        );
        sessionStorage.removeItem("reservaAfterPerfil");

        if (typeof guardarReserva === "function") {
          guardarReserva(reservaPendiente);
        } else {
          const usuario = obtenerUsuarioActivo();
          let reservas = JSON.parse(localStorage.getItem("reservas")) || [];
          reservas.push({
            ...reservaPendiente,
            usuarioEmail: usuario.email,
            usuarioNombre: usuario.nombre,
            fechaRegistro: new Date().toISOString(),
          });
          localStorage.setItem("reservas", JSON.stringify(reservas));
        }

        if (typeof actualizarNotificaciones === "function")
          actualizarNotificaciones();

        alert("Los datos han sido guardados.");

        // Refrescar el Navbar para que muestre el nombre actualizado
        inicializarNavbar();
        return;
      } catch (err) {
        console.error("Error procesando reserva pendiente:", err);
      }
    }

    alert("Los datos han sido guardados.");

    // Refrescar el Navbar para que muestre el nombre actualizado
    inicializarNavbar();
  });
}

// --- RUTA BASE PARA GITHUB PAGES ---
const rutaBase = window.location.hostname.includes("github.io")
  ? "/Homepage---M-A" // ← CAMBIA esto por el nombre de tu repo
  : "";

window.cargarSeccion = async function (archivo, ancla = null) {
  const mainContent = document.getElementById("main-content");

  try {
    const response = await fetch(`${rutaBase}/secciones/${archivo}`);

    if (!response.ok) {
      throw new Error("Archivo no encontrado");
    }

    mainContent.innerHTML = await response.text();

    // Carrusel superior

    if (document.querySelector(".carrusel-container")) {
      iniciarCarruselVisual();
    }

    // Inicializaciones
    if (archivo === "perfil.html") {
      inicializarLogicaPerfil();

      if (window.innerWidth < 992) {
        activarNav("nav-perfil");
      }
    }

    if (archivo === "reservas.html") {
      inicializarLogicaReserva();

      if (window.innerWidth < 992) {
        activarNav("nav-mis-reservas");
      } else {
        activarNav("nav-agendar");
      }
    }

    if (document.querySelector(".barbers-track")) inicializarCarousel();

    // ===== NAVBAR ACTIVO =====

    if (archivo === "servicios.html") {
      activarNav("nav-servicios");
    } else if (archivo === "reservas.html") {
      activarNav("nav-agendar");
    } else if (archivo === "info.html") {
      // Activa Inicio por defecto
      activarNav("nav-inicio");

      // Activa el detector automático
      activarDetectorSecciones();

      // Si viene desde Barberos o Marca
      if (ancla) {
        setTimeout(() => {
          const elemento = document.querySelector(ancla);

          if (elemento) {
            elemento.scrollIntoView({
              behavior: "smooth",
            });
          }
        }, 100);
      }
    }
  } catch (err) {
    console.error(err);
  }
};

// --- VARIABLES GLOBALES PARA MODALES (Fuera de la función) ---
let pseModal_res, cardModal_res, successModal_res;

// --- LÓGICA DE RESERVAS (Encapsulada) ---
function inicializarModuloReservas() {
  // 1. SELECTORES
  const calendarDays = document.getElementById("calendarDays");
  const currentMonthYear = document.getElementById("currentMonthYear");
  const prevMonth = document.getElementById("prevMonth");
  const nextMonth = document.getElementById("nextMonth");
  const hoursGrid = document.getElementById("hoursGrid");

  // Elementos de resumen y estado
  const summaryService = document.getElementById("summaryService");
  const summaryBarber = document.getElementById("summaryBarber");
  const summaryDate = document.getElementById("summaryDate");
  const summaryHour = document.getElementById("summaryHour");
  const summaryPayment = document.getElementById("summaryPayment");
  const selectedMethodDisplay = document.getElementById(
    "selectedMethodDisplay",
  );

  let estado = { fecha: "", hora: "", metodo: "" };
  let mesOffset = 0;

  // Inicializar instancias de modales de Bootstrap
  const pseModal = new bootstrap.Modal(document.getElementById("pseModal"));
  const cardModal = new bootstrap.Modal(document.getElementById("cardModal"));
  const successModal = new bootstrap.Modal(
    document.getElementById("successModal"),
  );

  // 2. FUNCIÓN PARA DIBUJAR EL CALENDARIO
  function renderizarCalendario() {
    const fechaBase = new Date();
    fechaBase.setMonth(fechaBase.getMonth() + mesOffset);

    const nombreMes = fechaBase.toLocaleDateString("es-ES", {
      month: "long",
      year: "numeric",
    });
    currentMonthYear.textContent =
      nombreMes.charAt(0).toUpperCase() + nombreMes.slice(1);

    calendarDays.innerHTML = "";

    const primerDia = new Date(
      fechaBase.getFullYear(),
      fechaBase.getMonth(),
      1,
    ).getDay();
    const diasEnMes = new Date(
      fechaBase.getFullYear(),
      fechaBase.getMonth() + 1,
      0,
    ).getDate();
    const offset = primerDia === 0 ? 6 : primerDia - 1;

    for (let i = 0; i < offset; i++) calendarDays.innerHTML += "<span></span>";

    const hoy = new Date();
    hoy.setHours(0, 0, 0, 0);

    for (let i = 1; i <= diasEnMes; i++) {
      const fechaActual = new Date(
        fechaBase.getFullYear(),
        fechaBase.getMonth(),
        i,
      );
      const btn = document.createElement("button");
      btn.className = "day";
      btn.textContent = i;

      if (fechaActual < hoy) {
        btn.disabled = true;
        btn.classList.add("disabled-day");
      } else {
        btn.addEventListener("click", () => {
          document
            .querySelectorAll(".day")
            .forEach((d) => d.classList.remove("selected-day"));
          btn.classList.add("selected-day");
          estado.fecha = fechaActual.toLocaleDateString("es-ES", {
            day: "numeric",
            month: "long",
            year: "numeric",
          });
          summaryDate.textContent = estado.fecha;
        });
      }
      calendarDays.appendChild(btn);
    }
  }

  // 3. NAVEGACIÓN MESES
  prevMonth.addEventListener("click", () => {
    if (mesOffset > 0) {
      mesOffset--;
      renderizarCalendario();
    }
  });
  nextMonth.addEventListener("click", () => {
    if (mesOffset < 1) {
      mesOffset++;
      renderizarCalendario();
    }
  });

  // 4. GENERAR HORAS
  const horas = [
    "08:00 AM",
    "09:00 AM",
    "10:00 AM",
    "11:00 AM",
    "12:00 PM",
    "01:00 PM",
    "02:00 PM",
    "03:00 PM",
    "04:00 PM",
    "05:00 PM",
    "06:00 PM",
    "07:00 PM",
  ];
  hoursGrid.innerHTML = "";
  horas.forEach((hora) => {
    const btn = document.createElement("button");
    btn.className = "hour-card";
    btn.textContent = hora;
    btn.addEventListener("click", () => {
      document
        .querySelectorAll(".hour-card")
        .forEach((h) => h.classList.remove("hour-selected"));
      btn.classList.add("hour-selected");
      estado.hora = hora;
      summaryHour.textContent = hora;
    });
    hoursGrid.appendChild(btn);
  });

  // 5. EVENTOS SELECTS Y PAGOS
  document
    .getElementById("servicio")
    .addEventListener(
      "change",
      (e) => (summaryService.textContent = e.target.value),
    );
  document
    .getElementById("barbero")
    .addEventListener(
      "change",
      (e) => (summaryBarber.textContent = e.target.value),
    );

  document.querySelectorAll(".payment-option").forEach((opcion) => {
    opcion.addEventListener("click", (e) => {
      e.preventDefault();

      console.log("CLICK EN:", opcion.dataset.method);

      estado.metodo = opcion.dataset.method;

      selectedMethodDisplay.textContent = estado.metodo;
      summaryPayment.textContent = estado.metodo;
    });
  });

  // 6. LÓGICA DEL BOTÓN RESERVAR CON MODALES
  document.getElementById("btnReservar").addEventListener("click", () => {
    if (!estado.fecha || !estado.hora || !estado.metodo) {
      alert("Por favor, selecciona fecha, hora y método de pago.");
    } else {
      if (estado.metodo === "PSE") {
        pseModal.show();
      } else if (estado.metodo === "Tarjeta de Crédito") {
        cardModal.show();
      } else {
        document.getElementById("input_fecha_seleccionada").value = estado.fecha;
        document.getElementById("input_hora_seleccionada").value = estado.hora;
        document.getElementById("input_metodo_pago").value = estado.metodo;

        document.getElementById("formReservas").submit();
      }
    }
  });

  // Eventos de botones dentro de los modales
  document.getElementById("btnPagarPSE")?.addEventListener("click", () => {

    if (!estado.fecha || !estado.hora || !estado.metodo) {
      alert("Faltan datos de reserva");
      return;
    }

    document.getElementById("input_fecha_seleccionada").value = estado.fecha;
    document.getElementById("input_hora_seleccionada").value = estado.hora;
    document.getElementById("input_metodo_pago").value = estado.metodo;

    pseModal.hide();

    document.getElementById("formReservas").submit();
  });

  document.getElementById("btnPagarCard")?.addEventListener("click", () => {

    if (!estado.fecha || !estado.hora || !estado.metodo) {
      alert("Faltan datos de reserva");
      return;
    }

    document.getElementById("input_fecha_seleccionada").value = estado.fecha;
    document.getElementById("input_hora_seleccionada").value = estado.hora;
    document.getElementById("input_metodo_pago").value = estado.metodo;

    cardModal.hide();

    document.getElementById("formReservas").submit();
  });

  renderizarCalendario();

  document
  .getElementById("btnVerMisReservas")
  ?.addEventListener("click", () => {

      successModal.hide();

      mostrarMisReservas(true);

  });
}

document.addEventListener("click", function(e){

    if(e.target.id === "confirmarCancelarReserva"){

        const modal = bootstrap.Modal.getInstance(
            document.getElementById("cancelReservationModal")
        );

        modal?.hide();

        cancelarReserva(reservaAEliminar);

    }

});

function activarNav(id) {
  document
    .querySelectorAll(".navbar .nav-link")
    .forEach((link) => link.classList.remove("active"));

  const enlace = document.getElementById(id);

  if (enlace) {
    enlace.classList.add("active");
  }
}

function activarDetectorSecciones() {
  const secciones = [
    { id: "inicio", nav: "nav-inicio" },
    { id: "barberos", nav: "nav-barberos" },
    { id: "marca", nav: "nav-marca" },
  ];

  function verificarSeccion() {
    const posicion = window.scrollY + 150;

    secciones.forEach((seccion) => {
      const elemento = document.getElementById(seccion.id);

      if (!elemento) return;

      const inicio = elemento.offsetTop;
      const fin = inicio + elemento.offsetHeight;

      if (posicion >= inicio && posicion < fin) {
        activarNav(seccion.nav);
      }
    });
  }

  window.addEventListener("scroll", verificarSeccion);

  // ← IMPORTANTE: ejecutarlo una vez al cargar
  verificarSeccion();
}

function activarSideMenu(id) {
  document
    .querySelectorAll("#side-menu .menu-items a")
    .forEach((link) => link.classList.remove("active"));

  const enlace = document.getElementById(id);

  if (enlace) {
    enlace.classList.add("active");
  }
}

function obtenerUsuarioActivo() {
  const sesion = JSON.parse(localStorage.getItem("sesionActiva")) || {};
  return {
    email: sesion.email || sesion.correo || "",
    nombre: sesion.nombre || "",
  };
}

/* guardar reservas */
function guardarReserva(reserva) {
  let reservas = JSON.parse(localStorage.getItem("reservas")) || [];
  const usuario = obtenerUsuarioActivo();

  reservas.push({
    ...reserva,
    usuarioEmail: usuario.email,
    usuarioNombre: usuario.nombre,
    fechaRegistro: new Date().toISOString(),
  });

  localStorage.setItem("reservas", JSON.stringify(reservas));

  actualizarNotificaciones();
}

function obtenerReservasUsuario() {
  const usuario = obtenerUsuarioActivo();
  const reservas = JSON.parse(localStorage.getItem("reservas")) || [];
  if (!usuario.email) return [];
  return reservas.filter((reserva) => reserva.usuarioEmail === usuario.email);
}

function mostrarMisReservas(desdeReserva = false) {

    if(desdeReserva){

        sessionStorage.setItem(
            "mostrarVolverAgendar",
            "true"
        );

    } else {

        sessionStorage.removeItem(
            "mostrarVolverAgendar"
        );

    }

    const mostrarBotonVolver =
        sessionStorage.getItem(
            "mostrarVolverAgendar"
        ) === "true";

  const mainContent = document.getElementById("main-content");

  const reservas = obtenerReservasUsuario();

  if (reservas.length === 0) {
    mainContent.innerHTML = `
            <section class="reservation-section">
                <div class="container">
                    <div class="no-reservas">
                        <h3>No tienes reservas registradas</h3>
                        <p>Cuando agendes una cita aparecerá aquí.</p>
                    </div>
                </div>
            </section>
        `;

    return;
  }

  mainContent.innerHTML = `
        <section class="reservation-section">
            <div class="container">
                <div class="mis-reservas-container">

                    <div class="text-center mb-4">

                        <h1 class="page-title m-0">
                            Mis <span class="text-gold">Reservas</span>
                        </h1>

                    </div>

                    ${reservas
                      .map(
                        (reserva, index) => `

                        <div class="reserva-card">

                            <div class="reserva-header">
                                <h3 class="reserva-title">
                                    Reserva #${index + 1}
                                </h3>
                            </div>

                            <div class="reserva-info">

                                <div class="reserva-item">
                                    <span>Servicio</span>
                                    <strong>${reserva.servicio}</strong>
                                </div>

                                <div class="reserva-item">
                                    <span>Barbero</span>
                                    <strong>${reserva.barbero}</strong>
                                </div>

                                <div class="reserva-item">
                                    <span>Fecha</span>
                                    <strong>${reserva.fecha}</strong>
                                </div>

                                <div class="reserva-item">
                                    <span>Hora</span>
                                    <strong>${reserva.hora}</strong>
                                </div>

                                <div class="reserva-item">
                                    <span>Método de pago</span>
                                    <strong>${reserva.metodo}</strong>
                                </div>

                            </div>

                            <div class="text-end mt-3">

                                <button
                                    class="btn-cancelar-reserva"
                                    onclick="abrirModalCancelar('${reserva.fechaRegistro}')">

                                    Cancelar reserva

                                </button>

                            </div>

                        </div>

                    `,
                      )
                      .join("")}

                      ${mostrarBotonVolver ? `

                          <div class="text-end mt-5">

                              <a href="#"
                                class="btn-volver-agendar"
                                onclick="
                                      sessionStorage.removeItem('mostrarVolverAgendar');
                                      window.cargarSeccion('reservas.html');
                                      return false;
                                ">

                                 Volver a Agendar →

                              </a>

                          </div>

                      ` : ""}

                </div>
            </div>

        </section>

        <div class="modal fade" id="cancelReservationModal" tabindex="-1">

            <div class="modal-dialog modal-dialog-centered">

                <div class="modal-content custom-modal">

                    <div class="modal-body text-center">

                        <h3 class="text-gold">
                            ¿Cancelar reserva?
                        </h3>

                        <p>
                            Esta acción eliminará la reserva permanentemente.
                        </p>

                        <div class="d-flex justify-content-center gap-3">

                            <button
                                class="btn btn-secondary"
                                data-bs-dismiss="modal">

                                Volver

                            </button>

                            <button
                                class="btn btn-danger"
                                id="confirmarCancelarReserva">

                                Sí, cancelar

                            </button>

                        </div>

                    </div>

                </div>

            </div>

        </div>
    `;
}

function abrirModalCancelar(idReserva){

    reservaAEliminar = idReserva;

    const modal = new bootstrap.Modal(
        document.getElementById("cancelReservationModal")
    );

    modal.show();

}

function cancelarReserva(idReserva){

    let reservas =
        JSON.parse(localStorage.getItem("reservas")) || [];

    const reservaCancelada =
        reservas.find(
            r => r.fechaRegistro === idReserva
        );

    reservas =
        reservas.filter(
            r => r.fechaRegistro !== idReserva
        );

    localStorage.setItem(
        "reservas",
        JSON.stringify(reservas)
    );

    let cancelaciones =
        JSON.parse(localStorage.getItem("cancelaciones")) || [];

    cancelaciones.unshift({

        fecha: new Date().toLocaleString(),

        servicio: reservaCancelada?.servicio,

        fechaReserva: reservaCancelada?.fecha,

        hora: reservaCancelada?.hora

    });

    localStorage.setItem(
        "cancelaciones",
        JSON.stringify(cancelaciones)
    );

    actualizarNotificaciones();

    mostrarMisReservas();

}

function actualizarNotificaciones() {

    const lista = document.getElementById("lista-notificaciones");
    if (!lista) return;

    const reservas = obtenerReservasUsuario();

    const cancelaciones =
        JSON.parse(
            localStorage.getItem("cancelaciones")
        ) || [];

    let html = "";

    reservas
        .slice()
        .reverse()
        .forEach((reserva) => {

            html += `
                <div class="notification-item border-bottom pb-2 mb-2">

                    <strong>📅 Reserva confirmada</strong>

                    <div>
                        ${reserva.servicio}
                    </div>

                    <small>
                        ${reserva.fecha} - ${reserva.hora}
                    </small>

                    <br>

                    <small>
                        👤 ${reserva.barbero}
                    </small>

                </div>
            `;

        });

    cancelaciones.forEach((cancelacion) => {

        html += `
            <div class="notification-item border-bottom pb-2 mb-2">

                <strong class="text-danger">
                    ❌ Reserva cancelada
                </strong>

                <div>
                    ${cancelacion.servicio}
                </div>

                <small>
                    ${cancelacion.fechaReserva}
                    - ${cancelacion.hora}
                </small>

            </div>
        `;

    });

    if (html === "") {

        lista.innerHTML =
            "No tienes notificaciones nuevas.";

        return;
    }

    lista.innerHTML = html;
}

// Esta función la llamas cada vez que inyectas HTML nuevo
function iniciarCarruselVisual() {
  const carrusel = document.querySelector(".carrusel-container");
  if (!carrusel) return;

  const images = carrusel.querySelectorAll("img");
  if (images.length === 0) return;

  let currentIndex = 0;

  // Limpiamos cualquier intervalo previo para evitar duplicados
  if (window.carruselInterval) clearInterval(window.carruselInterval);

  window.carruselInterval = setInterval(() => {
    images[currentIndex].classList.remove("active");
    currentIndex = (currentIndex + 1) % images.length;
    images[currentIndex].classList.add("active");
    console.log("Carrusel rotando, imagen:", currentIndex);
  }, 2000);
}