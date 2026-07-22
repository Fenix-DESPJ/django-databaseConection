// --- VARIABLES GLOBALMENTE DECLARADAS PARA MODALES BOOTSTRAP ---
let pseModal, cardModal, reservationToast;

// --- ESTADO DE DISPONIBILIDAD (viene del backend: días habilitados por el admin,
//     horas configuradas y horas ya ocupadas por barbero/fecha) ---
let disponibilidad = { horas_disponibles: [], dias_habilitados: [], horas_ocupadas: [] };

async function cargarDisponibilidad(barberoId, fechaStr) {
  let url = `/reservas/disponibilidad/?`;
  if (barberoId) url += `barbero=${barberoId}&`;
  if (fechaStr) url += `fecha=${fechaStr}`;
  try {
    const resp = await fetch(url);
    disponibilidad = await resp.json();
  } catch (e) {
    console.error("Error al cargar disponibilidad:", e);
  }
  return disponibilidad;
}

document.addEventListener("DOMContentLoaded", () => {
  // Inicialización del módulo si la vista de reservas está activa en el DOM
  if (document.getElementById("reservation-module-wrapper")) {
    inicializarModuloReservas();
  }
});

async function inicializarModuloReservas() {
  // --- SELECTORES DEL DOM ---
  const formReservas = document.getElementById("formReservas");
  const calendarDays = document.getElementById("calendarDays");
  const currentMonthYear = document.getElementById("currentMonthYear");
  const prevMonth = document.getElementById("prevMonth");
  const nextMonth = document.getElementById("nextMonth");
  const hoursGrid = document.getElementById("hoursGrid");

  // Selectores de los elementos Select generados por Django
  const selectServicio = document.getElementById("servicio");
  const selectBarbero = document.getElementById("barbero");

  // Selectores para los Inputs Ocultos (Hidden) destinados al POST de Django
  const inputFecha = document.getElementById("input_fecha_seleccionada");
  const inputHora = document.getElementById("input_hora_seleccionada");
  const inputMetodoPago = document.getElementById("input_metodo_pago");

  // Selectores del Resumen de Reserva lateral derecho
  const summaryService = document.getElementById("summaryService");
  const summaryBarber = document.getElementById("summaryBarber");
  const summaryDate = document.getElementById("summaryDate");
  const summaryHour = document.getElementById("summaryHour");
  const summaryPayment = document.getElementById("summaryPayment");
  const selectedMethodDisplay = document.getElementById("selectedMethodDisplay");

  // Botón principal del flujo
  const btnReservar = document.getElementById("btnReservar");

  // --- ESTADO INTERNO DEL CLIENTE ---
  let estadoReserva = {
    fecha: "",
    hora: "",
    metodoPago: ""
  };

  let mesOffset = 0;

  // --- CARGA INICIAL DE DISPONIBILIDAD (días habilitados por el admin) ---
  // Al inicio aún no hay fecha seleccionada, así que pasamos null.
  await cargarDisponibilidad(selectBarbero ? selectBarbero.value : null, null);
  actualizarEstadoBarberos();
  renderizarCalendario();
  renderizarHoras();

  // --- NUEVA LÓGICA: Auto-seleccionar servicio desde URL ---
  const urlParams = new URLSearchParams(window.location.search);
  const servicioId = urlParams.get('servicio_id');

  if (servicioId && selectServicio) {
    selectServicio.value = servicioId;
    if (selectServicio.value === servicioId) {
      selectServicio.dispatchEvent(new Event('change'));
    }
  }

  // --- INICIALIZACIÓN DE MODALES Y TOASTS (BOOTSTRAP) ---
  pseModal = new bootstrap.Modal(document.getElementById("pseModal"));
  cardModal = new bootstrap.Modal(document.getElementById("cardModal"));

  const toastEl = document.getElementById("reservationToast");
  if (toastEl) {
    reservationToast = new bootstrap.Toast(toastEl, { delay: 3000 });
  }

  // --- NAVEGACIÓN DE MES (registrada UNA sola vez, no en cada render) ---
  if (prevMonth) {
    prevMonth.addEventListener("click", () => {
      if (prevMonth.disabled) return;
      mesOffset--;
      renderizarCalendario();
    });
  }

  if (nextMonth) {
    nextMonth.addEventListener("click", () => {
      if (nextMonth.disabled) return;
      mesOffset++;
      renderizarCalendario();
    });
  }

  // --- ESCUCHADORES DE SELECTS (SINCRO CON EL RESUMEN) ---
  if (selectServicio) {
    actualizarTextoServicio();
    selectServicio.addEventListener("change", actualizarTextoServicio);
  }

  if (selectBarbero) {
    actualizarTextoBarbero();
    selectBarbero.addEventListener("change", async () => {
      actualizarTextoBarbero();
      // Si ya hay fecha seleccionada, refrescamos las horas ocupadas de ESTE barbero en esa fecha
      if (estadoReserva.fecha) {
        await cargarDisponibilidad(selectBarbero.value, estadoReserva.fecha);
        renderizarHoras();
      }
    });
  }

  function actualizarTextoServicio() {
    if (summaryService && selectServicio) {
      const textoSeleccionado = selectServicio.options[selectServicio.selectedIndex].text;
      summaryService.textContent = selectServicio.value ? textoSeleccionado : "Selecciona un servicio";
    }
  }

  function actualizarTextoBarbero() {
    if (summaryBarber && selectBarbero) {
      const textoSeleccionado = selectBarbero.options[selectBarbero.selectedIndex].text;
      summaryBarber.textContent = selectBarbero.value ? textoSeleccionado : "Selecciona tu barbero";
    }
  }

  // --- ESCUCHA DEL DROPDOWN PERSONALIZADO DE MÉTODOS DE PAGO ---
  const paymentOptions = document.querySelectorAll(".payment-option");
  paymentOptions.forEach(option => {
    option.addEventListener("click", (e) => {
      e.preventDefault();
      const metodo = option.getAttribute("data-method");

      estadoReserva.metodoPago = metodo;
      if (inputMetodoPago) inputMetodoPago.value = metodo;

      if (selectedMethodDisplay) selectedMethodDisplay.textContent = metodo;
      if (summaryPayment) summaryPayment.textContent = metodo;
    });
  });

  // Validar cuando confirman dentro del modal de PSE o Tarjeta
  const btnPagarPSE = document.getElementById("btnPagarPSE");
  if (btnPagarPSE) {
    btnPagarPSE.addEventListener("click", () => {
      inputMetodoPago.value = "PSE";
      if (selectedMethodDisplay) selectedMethodDisplay.textContent = "PSE";
      if (summaryPayment) summaryPayment.textContent = "PSE";
    });
  }

  const btnPagarCard = document.getElementById("btnPagarCard");
  if (btnPagarCard) {
    btnPagarCard.addEventListener("click", () => {
      inputMetodoPago.value = "Tarjeta de Crédito";
      if (selectedMethodDisplay) selectedMethodDisplay.textContent = "Tarjeta de Crédito";
      if (summaryPayment) summaryPayment.textContent = "Tarjeta de Crédito";
    });
  }

  // --- RENDERIZACIÓN DINÁMICA DEL CALENDARIO ---
  function renderizarCalendario() {
    const fechaBase = new Date();
    fechaBase.setDate(1); // evita bugs de "overflow" de día al cambiar de mes
    fechaBase.setHours(0, 0, 0, 0);
    fechaBase.setMonth(fechaBase.getMonth() + mesOffset);

    const nombreMes = fechaBase.toLocaleDateString("es-ES", {
      month: "long",
      year: "numeric",
    });

    if (currentMonthYear) {
      currentMonthYear.textContent = nombreMes.charAt(0).toUpperCase() + nombreMes.slice(1);
    }

    if (!calendarDays) return;
    calendarDays.innerHTML = "";

    let primerDia = new Date(fechaBase.getFullYear(), fechaBase.getMonth(), 1).getDay();
    const diasEnMes = new Date(fechaBase.getFullYear(), fechaBase.getMonth() + 1, 0).getDate();
    let offset = primerDia === 0 ? 6 : primerDia - 1;

    for (let i = 0; i < offset; i++) {
      const divVacio = document.createElement("div");
      divVacio.classList.add("day", "empty");
      calendarDays.appendChild(divVacio);
    }

    const hoy = new Date();
    hoy.setHours(0, 0, 0, 0);

    // --- Límite máximo de reserva = un mes desde hoy ---
    const fechaMaxima = new Date(hoy);
    fechaMaxima.setMonth(fechaMaxima.getMonth() + 1);

    for (let dia = 1; dia <= diasEnMes; dia++) {
      const fechaIteradaObj = new Date(fechaBase.getFullYear(), fechaBase.getMonth(), dia);

      const mesFormateado = String(fechaBase.getMonth() + 1).padStart(2, '0');
      const diaFormateado = String(dia).padStart(2, '0');
      const fechaIterada = `${fechaBase.getFullYear()}-${mesFormateado}-${diaFormateado}`;

      const btonDia = document.createElement("button");
      btonDia.type = "button";
      btonDia.classList.add("day");
      btonDia.textContent = dia;

      const estaHabilitado = disponibilidad.dias_habilitados.includes(fechaIterada);
      const fueraDeRango = fechaIteradaObj < hoy || fechaIteradaObj > fechaMaxima;

      if (fueraDeRango || !estaHabilitado) {
        btonDia.classList.add("disabled");
        btonDia.disabled = true;
        btonDia.title = fueraDeRango
          ? "Fuera del rango permitido para reservar (hoy hasta un mes después)"
          : "Día no habilitado por el administrador";
      }

      if (estadoReserva.fecha === fechaIterada) {
        btonDia.classList.add("selected");
      }

      if (!btonDia.disabled) {
        btonDia.addEventListener("click", async () => {
          document.querySelectorAll(".day").forEach(b => b.classList.remove("selected"));
          btonDia.classList.add("selected");

          estadoReserva.fecha = fechaIterada;
          if (inputFecha) inputFecha.value = fechaIterada;
          if (summaryDate) summaryDate.textContent = fechaIterada;

          await cargarDisponibilidad(selectBarbero ? selectBarbero.value : null, fechaIterada);
          renderizarHoras();
        });
      }

      calendarDays.appendChild(btonDia);
    }

    actualizarBotonesNavegacionMes(fechaBase, hoy, fechaMaxima);
  }

  // Solo actualiza el estado disabled de las flechas; NO registra listeners aquí
  function actualizarBotonesNavegacionMes(fechaBase, hoy, fechaMaxima) {
    const inicioMesVisible = new Date(fechaBase.getFullYear(), fechaBase.getMonth(), 1);

    if (prevMonth) {
      const inicioMesHoy = new Date(hoy.getFullYear(), hoy.getMonth(), 1);
      const puedeRetroceder = inicioMesVisible > inicioMesHoy;
      prevMonth.disabled = !puedeRetroceder;
      prevMonth.classList.toggle("disabled", !puedeRetroceder);
    }

    if (nextMonth) {
      const inicioMesMax = new Date(fechaMaxima.getFullYear(), fechaMaxima.getMonth(), 1);
      const puedeAvanzar = inicioMesVisible < inicioMesMax;
      nextMonth.disabled = !puedeAvanzar;
      nextMonth.classList.toggle("disabled", !puedeAvanzar);
    }
  }

  // --- RENDERIZACIÓN DE LAS HORAS EN LA GRILLA ---
  function renderizarHoras() {
    if (!hoursGrid) return;
    hoursGrid.innerHTML = "";

    const listadoHoras = (disponibilidad.horas_disponibles && disponibilidad.horas_disponibles.length)
        ? disponibilidad.horas_disponibles
        : ["08:00", "09:00", "10:00", "11:00", "14:00", "15:00", "16:00", "17:00"];

    const ocupadas = disponibilidad.horas_ocupadas || [];
    const ahora = new Date();
    const fechaSeleccionada = estadoReserva.fecha ? new Date(estadoReserva.fecha + "T00:00:00") : null;
    const esHoy = fechaSeleccionada && fechaSeleccionada.toDateString() === ahora.toDateString();

    listadoHoras.forEach(hora => {
      const [h, m] = hora.split(":").map(Number);
      const btonHora = document.createElement("button");
      btonHora.type = "button";
      btonHora.classList.add("hour-btn");
      btonHora.textContent = hora;

      let bloqueadaPorHoraActual = false;
      if (esHoy) {
        const horaCita = new Date(fechaSeleccionada);
        horaCita.setHours(h, m, 0, 0);
        bloqueadaPorHoraActual = (horaCita - ahora) < 3600000; // menos de 1 hora de anticipación
      }

      if (ocupadas.includes(hora)) {
        btonHora.classList.add("disabled");
        btonHora.disabled = true;
        btonHora.title = "Ese barbero ya tiene una cita a esta hora";
      } else if (bloqueadaPorHoraActual) {
        btonHora.classList.add("disabled");
        btonHora.disabled = true;
      } else {
        if (estadoReserva.hora === hora) btonHora.classList.add("selected");
        btonHora.addEventListener("click", () => {
          document.querySelectorAll(".hour-btn").forEach(b => b.classList.remove("selected"));
          btonHora.classList.add("selected");
          estadoReserva.hora = hora;
          if (inputHora) inputHora.value = hora;
          if (summaryHour) summaryHour.textContent = hora;
        });
      }
      hoursGrid.appendChild(btonHora);
    });
  }

  // --- ENVÍO REAL DE LA RESERVA: recarga solo en caso de error, para refrescar disponibilidad ---
  const errorModalEl = document.getElementById("errorReservaModal");
  if (errorModalEl) {
    errorModalEl.addEventListener("hidden.bs.modal", () => {
      if (errorModalEl.dataset.debeRecargar === "true") {
        window.location.reload();
      }
    });
  }

  // --- FLUJO DE CONTROL: BOTÓN FINAL DE RESERVA (validación + envío + resultado) ---
  if (btnReservar) {
    btnReservar.addEventListener("click", async () => {
      if (!selectServicio || !selectServicio.value) {
        alert("Por favor, selecciona un servicio.");
        return;
      }
      if (!selectBarbero || !selectBarbero.value) {
        alert("Por favor, selecciona un barbero de preferencia.");
        return;
      }
      if (!inputFecha || !inputFecha.value) {
        alert("Por favor, selecciona un día válido en el calendario.");
        return;
      }
      if (!inputHora || !inputHora.value) {
        alert("Por favor, selecciona un horario disponible.");
        return;
      }
      if (!inputMetodoPago || !inputMetodoPago.value) {
        alert("Por favor, selecciona tu método de pago.");
        return;
      }

      // Evita doble click mientras se procesa
      btnReservar.disabled = true;
      const textoOriginal = btnReservar.innerHTML;
      btnReservar.innerHTML = "Procesando...";

      const formData = new FormData(formReservas);
      try {
        const resp = await fetch(formReservas.action || window.location.href, {
          method: "POST",
          headers: { "X-Requested-With": "XMLHttpRequest" },
          body: formData
        });
        const data = await resp.json();

        if (data.ok) {
          // --- ÉXITO: solo el toast ---
          if (reservationToast) reservationToast.show();
          setTimeout(() => {
            window.location.href = data.redirect;
          }, 1800);
        } else {
          // --- ERROR: solo el modal ---
          document.getElementById("errorReservaMensaje").textContent = data.error;
          errorModalEl.dataset.debeRecargar = "true";
          new bootstrap.Modal(errorModalEl).show();
          btnReservar.disabled = false;
          btnReservar.innerHTML = textoOriginal;
        }
      } catch (err) {
        document.getElementById("errorReservaMensaje").textContent = "Error de conexión, intenta de nuevo.";
        errorModalEl.dataset.debeRecargar = "false";
        new bootstrap.Modal(errorModalEl).show();
        btnReservar.disabled = false;
        btnReservar.innerHTML = textoOriginal;
      }
    });
  }

  // --- Deshabilitar barberos con agenda completa o desactivados por el admin ese día ---
  function actualizarEstadoBarberos() {
    if (!disponibilidad.barberos_estado || !selectBarbero) return;

    disponibilidad.barberos_estado.forEach(b => {
      const opcion = selectBarbero.querySelector(`option[value="${b.id}"]`);
      if (!opcion) return;

      if (!b.disponible) {
        opcion.disabled = true;
        opcion.textContent = opcion.textContent.replace(/ \(No disponible.*\)$/, '');
        opcion.textContent += b.motivo === 'admin' ? " (No disponible este día)" : " (Agenda completa)";
        if (selectBarbero.value === String(b.id)) {
          selectBarbero.value = "";
          estadoReserva.hora = "";
          if (inputHora) inputHora.value = "";
          actualizarTextoBarbero();
        }
      } else {
        opcion.disabled = false;
        opcion.textContent = opcion.textContent.replace(/ \((No disponible este día|Agenda completa)\)$/, '');
      }
    });
  }
}

/* Estado Centralizado */
let modoActual = null; // 'editar', 'borrar', o null

function cambiarModo(nuevoModo) {
    if (modoActual === nuevoModo) {
        desactivarModos();
        return;
    }

    desactivarModos();
    modoActual = nuevoModo;

    const btnEditar = document.getElementById('btn-editar-toggle');
    const btnBorrar = document.querySelector('.btn-danger');
    const tarjetas = document.querySelectorAll('.card-precio');

    if (modoActual === 'editar') {
        btnEditar.innerText = "Cancelar Edición";
        tarjetas.forEach(c => {
            c.classList.add('border-editar');
            c.style.cursor = "pointer";
            c.onclick = function() {
                abrirModalEditar(
                    this.getAttribute('data-id'),
                    this.getAttribute('data-nombre'),
                    this.getAttribute('data-precio'),
                    this.getAttribute('data-duracion'),
                    this.getAttribute('data-tipo')
                );
            };
        });
    }
    else if (modoActual === 'borrar') {
        btnBorrar.innerText = "Cancelar Borrado";
        tarjetas.forEach(c => {
            c.classList.add('border-borrar');
            c.style.cursor = "pointer";
            c.onclick = function() {
                const id = this.getAttribute('data-id');
                if(confirm('¿Seguro que deseas eliminar este servicio?')) {
                    const url = document.querySelector('[data-url-eliminar]').dataset.urlEliminar;
                    window.location.href = url.replace('0', id);
                }
            };
        });
    }
}

function desactivarModos() {
    modoActual = null;

    const btnEditar = document.getElementById('btn-editar-toggle');
    const btnBorrar = document.querySelector('.btn-danger');
    if (btnEditar) btnEditar.innerText = "Editar Servicio";
    if (btnBorrar) btnBorrar.innerText = "Borrar Servicio";

    const tarjetas = document.querySelectorAll('.card-precio');
    tarjetas.forEach(c => {
        c.classList.remove('border-editar', 'border-borrar');
        c.style.cursor = "default";
        c.onclick = null;
    });
}

let bsModalInstance = null;

function abrirModalEditar(id, nombre, precio, duracion, tipo) {
    const modalElement = document.getElementById('modalServicio');
    const form = document.getElementById('formServicio');
    const titulo = document.getElementById('modalServicioLabel');

    titulo.innerText = "Editar Servicio: " + nombre;
    const urlBase = document.getElementById('url-data').getAttribute('data-editar-base');
    form.action = urlBase.replace('0', id);

    const campos = {
        'nombreservicio': nombre,
        'precio': precio,
        'duracion': duracion,
        'tiposervicio': tipo
    };

    Object.keys(campos).forEach(key => {
        const input = form.querySelector(`[name="${key}"]`);
        if (input) input.value = campos[key];
    });

    const bsModal = bootstrap.Modal.getOrCreateInstance(modalElement);
    document.body.appendChild(modalElement);
    bsModal.show();
}

function prepararModalCrear() {
    const modalElement = document.getElementById('modalServicio');
    const form = document.getElementById('formServicio');
    const titulo = document.getElementById('modalServicioLabel');

    titulo.innerText = "Nuevo Servicio";
    form.action = document.getElementById('url-data').getAttribute('data-crear');
    form.reset();

    document.body.appendChild(modalElement);

    const bsModal = bootstrap.Modal.getOrCreateInstance(modalElement);
    bsModal.show();
}

document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.card-precio').forEach(card => {
        card.addEventListener('click', function() {
            if (modoActual === 'editar') {
                const id = this.getAttribute('data-id');
                const nombre = this.getAttribute('data-nombre');
                const precio = this.getAttribute('data-precio');
                const duracion = this.getAttribute('data-duracion');
                const tipo = this.getAttribute('data-tipo');

                abrirModalEditar(id, nombre, precio, duracion, tipo);
            }
        });
    });
});

/* js reportes admin */
document.addEventListener('DOMContentLoaded', function() {
    if (typeof Chart === 'undefined') {
        console.error("Chart.js no se ha cargado. Revisa tu etiqueta <script> en base.html");
        return;
    }

    const el = document.getElementById('datos-reporte');
    const canvas = document.getElementById('graficoIngresos');

    if (el && canvas) {
        try {
            const nombres = JSON.parse(el.dataset.nombres);
            const totales = JSON.parse(el.dataset.totales);

            const ctx = canvas.getContext('2d');

            new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: nombres,
                    datasets: [{
                        label: 'Ingresos ($)',
                        data: totales,
                        backgroundColor: '#ffc107',
                        borderRadius: 5
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: { beginAtZero: true, ticks: { color: '#ffffff' } },
                        x: { ticks: { color: '#ffffff' } }
                    }
                }
            });
        } catch (e) {
            console.error("Error al procesar los datos de la gráfica:", e);
        }
    } else {
        console.error("No se encontró el contenedor de datos o el canvas.");
    }
});

document.addEventListener("DOMContentLoaded", function() {
    const alerts = document.querySelectorAll('.alert');

    alerts.forEach(function(alert) {
        setTimeout(function() {
            if (typeof bootstrap !== 'undefined' && bootstrap.Alert) {
                const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
                bsAlert.close();
            } else {
                alert.style.transition = "opacity 0.5s ease";
                alert.style.opacity = "0";
                setTimeout(() => alert.remove(), 500);
            }
        }, 3000);
    });
});

document.querySelectorAll('.toggle-password').forEach(button => {
    button.addEventListener('click', function() {
        const input = this.parentElement.querySelector('input');
        const icon = this.querySelector('i');

        if (input.type === 'password') {
            input.type = 'text';
            icon.classList.remove('bi-eye-slash');
            icon.classList.add('bi-eye');
        } else {
            input.type = 'password';
            icon.classList.remove('bi-eye');
            icon.classList.add('bi-eye-slash');
        }
    });
});

/* --- Carrusel de reseñas/opiniones: loop infinito, sin autoplay --- */
document.addEventListener("DOMContentLoaded", () => {
    const dataScript = document.getElementById('resenas-data');
    const slotPrev = document.getElementById('resenaSlotPrev');
    const slotCenter = document.getElementById('resenaSlotCenter');
    const slotNext = document.getElementById('resenaSlotNext');
    const track = document.getElementById('resenasTrack');
    const prevBtn = document.getElementById('resenaPrevBtn');
    const nextBtn = document.getElementById('resenaNextBtn');

    if (!dataScript || !slotPrev || !slotCenter || !slotNext || !track || !prevBtn || !nextBtn) {
        return; // No hay sección de reseñas en esta página (o no hay opiniones aún)
    }

    let resenas = [];
    try {
        resenas = JSON.parse(dataScript.textContent);
    } catch (e) {
        console.error('No se pudieron leer las reseñas:', e);
        return;
    }

    const total = resenas.length;
    if (!total) return;

    let currentIndex = 0;

    // Índice circular: siempre cae dentro de [0, total-1], sin importar el offset
    function indiceCircular(offset) {
        return ((currentIndex + offset) % total + total) % total;
    }

    function renderEstrellas(cantidad) {
        let html = '';
        for (let i = 1; i <= 5; i++) {
            html += `<i class="bi ${i <= cantidad ? 'bi-star-fill' : 'bi-star'}"></i>`;
        }
        return html;
    }

    function renderTarjeta(slotEl, resena) {
        slotEl.innerHTML = `
            <div class="resena-card">
                <div class="resena-estrellas mb-2">${renderEstrellas(resena.estrellas)}</div>
                <p class="resena-comentario">"${resena.comentario}"</p>
                <p class="resena-cliente mb-0">${resena.cliente}</p>
                <p class="resena-fecha">${resena.fecha}</p>
            </div>
        `;
    }

    function pintarCarrusel() {
        // Con 1 o 2 reseñas no tiene sentido mostrar prev/next duplicados
        slotPrev.style.visibility = total > 2 ? 'visible' : 'hidden';
        slotNext.style.visibility = total > 2 ? 'visible' : 'hidden';
        prevBtn.disabled = total <= 1;
        nextBtn.disabled = total <= 1;

        renderTarjeta(slotPrev, resenas[indiceCircular(-1)]);
        renderTarjeta(slotCenter, resenas[indiceCircular(0)]);
        renderTarjeta(slotNext, resenas[indiceCircular(1)]);
    }

    function irA(offset) {
        if (total <= 1) return;
        currentIndex = indiceCircular(offset);

        // Pequeño fundido para que el cambio de tarjeta se sienta fluido,
        // en vez de un salto brusco de contenido
        track.classList.add('is-changing');
        window.setTimeout(() => {
            pintarCarrusel();
            track.classList.remove('is-changing');
        }, 180);
    }

    prevBtn.addEventListener('click', () => irA(-1));
    nextBtn.addEventListener('click', () => irA(1));

    // Render inicial. Ningún setInterval/autoplay: el movimiento solo
    // ocurre cuando el usuario hace clic en las flechas.
    pintarCarrusel();
});

/* Carruseles y mas estilo*/
document.addEventListener("DOMContentLoaded", () => {
    const images = document.querySelectorAll('.carrusel-container img');
    let currentIndex = 0;
    if (images.length) {
        setInterval(() => {
            images[currentIndex].classList.remove('active');
            currentIndex = (currentIndex + 1) % images.length;
            images[currentIndex].classList.add('active');
        }, 4000);
    }

    const track = document.querySelector('.barbers-track');
    const prevBtn = document.getElementById('prevBtn');
    const nextBtn = document.getElementById('nextBtn');

    if (track && prevBtn && nextBtn) {
        nextBtn.addEventListener('click', () => {
            track.scrollBy({ left: 300, behavior: 'smooth' });
        });

        prevBtn.addEventListener('click', () => {
            track.scrollBy({ left: -300, behavior: 'smooth' });
        });
    }
});

document.addEventListener("DOMContentLoaded", () => {
    const track = document.querySelector('.barbers-track');
    const cards = document.querySelectorAll('.barber-card');
    const nextBtn = document.getElementById('nextBtn');
    const prevBtn = document.getElementById('prevBtn');
    const dotsContainer = document.getElementById('carouselDots');

    if (!track || !cards.length || !nextBtn || !prevBtn || !dotsContainer) return;

    const itemsPerView = 3;
    const totalGroups = Math.ceil(cards.length / itemsPerView);
    let currentGroup = 0;

    for (let i = 0; i < totalGroups; i++) {
        const dot = document.createElement('div');
        dot.classList.add('dot');
        if (i === 0) dot.classList.add('active');
        dot.addEventListener('click', () => {
            currentGroup = i;
            updateCarousel();
        });
        dotsContainer.appendChild(dot);
    }

    const dots = document.querySelectorAll('.dot');

    function updateCarousel() {
        const cardWidth = cards[0].offsetWidth + 20;
        track.scrollTo({
            left: currentGroup * (cardWidth * itemsPerView),
            behavior: 'smooth'
        });

        dots.forEach((dot, index) => {
            dot.classList.toggle('active', index === currentGroup);
        });
    }

    nextBtn.addEventListener('click', () => {
        if (currentGroup < totalGroups - 1) {
            currentGroup++;
            updateCarousel();
        }
    });

    prevBtn.addEventListener('click', () => {
        if (currentGroup > 0) {
            currentGroup--;
            updateCarousel();
        }
    });
});

// Este script soluciona el bloqueo permanentemente
document.addEventListener('click', function (e) {
    if (e.target.classList.contains('modal-backdrop')) {
        const modal = document.querySelector('.modal.show');
        if (modal) {
            const bsModal = bootstrap.Modal.getInstance(modal);
            if (bsModal) bsModal.hide();
        }
    }
});

// Limpieza total al cerrar cualquier modal
document.addEventListener('hidden.bs.modal', function () {
    const backdrop = document.querySelector('.modal-backdrop');
    if (backdrop) {
        backdrop.remove();
    }
    document.body.classList.remove('modal-open');
    document.body.style.removeProperty('overflow');
    document.body.style.removeProperty('padding-right');
});

function manejarReserva(event) {
    const boton = event.currentTarget;
    const tieneSesion = boton.getAttribute('data-sesion') === 'true';
    const urlReserva = boton.getAttribute('data-url-reserva');

    if (!tieneSesion) {
        event.preventDefault();
        const authModal = new bootstrap.Modal(document.getElementById('authModal'));
        authModal.show();
    } else {
        window.location.href = urlReserva;
    }
}

/* --- Restricciones de tipo de dato en inputs (letras / números / tarjeta / expiry) --- */
document.addEventListener("DOMContentLoaded", () => {
    // Solo letras, tildes, ñ y espacios (nombres, apellidos, titular de tarjeta, etc.)
    document.querySelectorAll('[data-solo="letras"]').forEach(input => {
        input.addEventListener("input", () => {
            input.value = input.value.replace(/[^A-Za-zÁÉÍÓÚáéíóúÑñÜü\s]/g, "");
        });
        input.addEventListener("paste", (e) => {
            const texto = (e.clipboardData || window.clipboardData).getData("text");
            if (/[^A-Za-zÁÉÍÓÚáéíóúÑñÜü\s]/.test(texto)) {
                e.preventDefault();
                input.value += texto.replace(/[^A-Za-zÁÉÍÓÚáéíóúÑñÜü\s]/g, "");
            }
        });
    });

    // Solo dígitos (teléfono, cédula, CVV, etc.)
    document.querySelectorAll('[data-solo="numeros"]').forEach(input => {
        input.addEventListener("input", () => {
            input.value = input.value.replace(/[^0-9]/g, "");
        });
        input.addEventListener("paste", (e) => {
            const texto = (e.clipboardData || window.clipboardData).getData("text");
            if (/[^0-9]/.test(texto)) {
                e.preventDefault();
                input.value += texto.replace(/[^0-9]/g, "");
            }
        });
    });

    // Número de tarjeta: solo dígitos, agrupados de 4 en 4 con espacio, máx 16 dígitos
    document.querySelectorAll('[data-solo="tarjeta"]').forEach(input => {
        input.addEventListener("input", () => {
            let valor = input.value.replace(/[^0-9]/g, "").slice(0, 16);
            valor = valor.replace(/(.{4})/g, "$1 ").trim();
            input.value = valor;
        });
        input.addEventListener("paste", (e) => {
            const texto = (e.clipboardData || window.clipboardData).getData("text");
            if (/[^0-9\s]/.test(texto)) {
                e.preventDefault();
            }
        });
    });

    // Fecha de expiración de tarjeta: solo dígitos, formato automático MM/AA
    document.querySelectorAll('[data-solo="expiry"]').forEach(input => {
        input.addEventListener("input", () => {
            let valor = input.value.replace(/[^0-9]/g, "").slice(0, 4);

            // Autocorrección del mes: si el primer dígito es > 1, asumimos que quiso escribir 0X
            if (valor.length === 1 && parseInt(valor[0], 10) > 1) {
                valor = "0" + valor;
            }
            // Limita el mes a 01-12
            if (valor.length >= 2) {
                let mes = parseInt(valor.slice(0, 2), 10);
                if (mes > 12) valor = "12" + valor.slice(2);
                if (mes === 0) valor = "01" + valor.slice(2);
            }

            if (valor.length >= 3) {
                valor = valor.slice(0, 2) + "/" + valor.slice(2);
            }
            input.value = valor;
        });
        input.addEventListener("paste", (e) => {
            const texto = (e.clipboardData || window.clipboardData).getData("text");
            if (/[^0-9/]/.test(texto)) {
                e.preventDefault();
            }
        });
    });
});

/* ============================================================
   SISTEMA DE NOTIFICACIONES (Campanita) — por perfil individual
   ============================================================
   - Cliente: ve la confirmación de SU propia reserva.
   - Barbero: ve cuando un cliente le agenda un servicio a ÉL.
   - Admin: ve cuando un barbero confirma una cita exitosamente.
   Cada usuario solo ve lo que el backend le devuelve filtrado por
   su propio idUsuario (ver views.listar_notificaciones), así que
   nunca se mezclan notificaciones entre perfiles distintos.
   ============================================================ */
document.addEventListener("DOMContentLoaded", () => {
    const panel = document.getElementById("notificaciones-panel");
    const lista = document.getElementById("lista-notificaciones");

    const botones = [
        document.getElementById("btnNotifDesktop"),
        document.getElementById("btnNotifMobile")
    ].filter(Boolean);

    const badges = [
        document.getElementById("badgeNotifDesktop"),
        document.getElementById("badgeNotifMobile")
    ].filter(Boolean);

    // Si no hay sesión iniciada, estos elementos no existen: no hacemos nada.
    if (!panel || botones.length === 0) return;

    const URL_LISTAR = panel.dataset.urlListar;
    const URL_MARCAR = panel.dataset.urlMarcar;

    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== "") {
            const cookies = document.cookie.split(";");
            for (let cookie of cookies) {
                cookie = cookie.trim();
                if (cookie.substring(0, name.length + 1) === (name + "=")) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    function actualizarBadges(cantidad) {
        badges.forEach(b => {
            if (cantidad > 0) {
                b.textContent = cantidad > 9 ? "9+" : cantidad;
                b.classList.remove("d-none");
            } else {
                b.classList.add("d-none");
            }
        });
    }

    function iconoPorTipo(tipo) {
        switch (tipo) {
            case "reserva_creada": return "bi-calendar-check-fill";   // Cliente
            case "nueva_cita": return "bi-scissors";                 // Barbero
            case "cita_confirmada": return "bi-patch-check-fill";    // Admin
            default: return "bi-info-circle-fill";
        }
    }

    async function cargarNotificaciones() {
        try {
            const resp = await fetch(URL_LISTAR, { headers: { "X-Requested-With": "XMLHttpRequest" } });
            const data = await resp.json();

            lista.innerHTML = "";

            if (!data.notificaciones || data.notificaciones.length === 0) {
                lista.innerHTML = `<div class="text-center text-muted py-3" style="font-size:0.85rem;">
                    No tienes notificaciones por ahora.
                </div>`;
            } else {
                data.notificaciones.forEach(n => {
                    const item = document.createElement("div");
                    item.classList.add("notification-item");
                    if (!n.leida) {
                        item.style.borderLeftColor = "#ffc600";
                    }
                    item.innerHTML = `
                        <strong><i class="bi ${iconoPorTipo(n.tipo)} me-2"></i>${n.mensaje}</strong>
                        <small>${n.fecha}</small>
                    `;
                    lista.appendChild(item);
                });
            }

            actualizarBadges(data.no_leidas || 0);
        } catch (e) {
            console.error("Error al cargar notificaciones:", e);
        }
    }

    async function marcarComoLeidas() {
        try {
            await fetch(URL_MARCAR, {
                method: "POST",
                headers: {
                    "X-Requested-With": "XMLHttpRequest",
                    "X-CSRFToken": getCookie("csrftoken")
                }
            });
            actualizarBadges(0);
        } catch (e) {
            console.error("Error al marcar notificaciones como leídas:", e);
        }
    }

    function togglePanel() {
        const abierto = panel.classList.contains("active");
        if (abierto) {
            panel.classList.remove("active");
        } else {
            panel.classList.add("active");
            cargarNotificaciones().then(() => {
                // Se marcan como leídas un momento después de abrir el panel
                setTimeout(marcarComoLeidas, 1500);
            });
        }
    }

    botones.forEach(btn => {
        btn.addEventListener("click", (e) => {
            e.stopPropagation();
            togglePanel();
        });
    });

    // Cierra el panel si el usuario hace clic fuera de él
    document.addEventListener("click", (e) => {
        if (
            panel.classList.contains("active") &&
            !panel.contains(e.target) &&
            !botones.includes(e.target)
        ) {
            panel.classList.remove("active");
        }
    });

    // Carga inicial silenciosa del contador (sin abrir el panel) + refresco automático
    cargarNotificaciones();
    setInterval(cargarNotificaciones, 30000); // cada 30 segundos
});

/* ============================================================
analisis_rostro.html: script.js para análisis de rostro
============================================================ */
document.addEventListener("DOMContentLoaded", () => {
    const overlay = document.getElementById("privacidadOverlay");
    const contenido = document.getElementById("contenidoAnalisis");
    const btnAceptar = document.getElementById("btnAceptarPrivacidad");

    const btnUsarCamara = document.getElementById("btnUsarCamara");
    const btnUsarArchivo = document.getElementById("btnUsarArchivo");
    const btnUsarPerfil = document.getElementById("btnUsarPerfil");
    const inputArchivo = document.getElementById("inputArchivo");

    const zonaCamara = document.getElementById("zonaCamara");
    const videoCamara = document.getElementById("videoCamara");
    const canvasCaptura = document.getElementById("canvasCaptura");
    const btnCapturar = document.getElementById("btnCapturar");

    const zonaPreview = document.getElementById("zonaPreview");
    const imgPreview = document.getElementById("imgPreview");
    const btnAnalizar = document.getElementById("btnAnalizar");
    const btnReintentar = document.getElementById("btnReintentar");

    const spinnerAnalisis = document.getElementById("spinnerAnalisis");
    const errorBox = document.getElementById("errorBox");
    const resultadoBox = document.getElementById("resultadoBox");
    const formaDetectada = document.getElementById("formaDetectada");
    const recomendacionTexto = document.getElementById("recomendacionTexto");
    const metricasChips = document.getElementById("metricasChips");

    let streamCamara = null;
    let blobCapturado = null;
    let usarPerfilSeleccionado = false;

    // --- Lee la URL real inyectada por Django vía data-attribute (NO {% url %} aquí) ---
    function obtenerUrlAnalizar() {
        return contenido.dataset.urlAnalizar;
    }

    // --- Lee el token CSRF real desde el input que Django ya renderizó en el HTML ---
    function obtenerCSRFToken() {
        const input = document.querySelector('[name=csrfmiddlewaretoken]');
        return input ? input.value : '';
    }

    // --- Lee la URL de la foto de perfil desde data-attribute (evita {% if %} en el JS) ---
    function obtenerUrlFotoPerfil() {
        return contenido.dataset.fotoPerfil || '';
    }

    // --- Aceptar aviso de privacidad ---
    btnAceptar.addEventListener("click", () => {
        overlay.remove();
        contenido.style.opacity = "1";
        contenido.style.pointerEvents = "auto";
    });

    function resetearVistas() {
        zonaCamara.classList.add("d-none");
        zonaPreview.classList.add("d-none");
        errorBox.classList.remove("visible");
        resultadoBox.classList.remove("visible");
        usarPerfilSeleccionado = false;
        blobCapturado = null;
        if (streamCamara) {
            streamCamara.getTracks().forEach(t => t.stop());
            streamCamara = null;
        }
    }

    // --- Opción: usar cámara ---
    btnUsarCamara.addEventListener("click", async () => {
        resetearVistas();
        try {
            streamCamara = await navigator.mediaDevices.getUserMedia({ video: true });
            videoCamara.srcObject = streamCamara;
            zonaCamara.classList.remove("d-none");
        } catch (err) {
            errorBox.textContent = "No se pudo acceder a la cámara. Verifica los permisos del navegador.";
            errorBox.classList.add("visible");
        }
    });

    btnCapturar.addEventListener("click", () => {
        canvasCaptura.width = videoCamara.videoWidth;
        canvasCaptura.height = videoCamara.videoHeight;
        canvasCaptura.getContext("2d").drawImage(videoCamara, 0, 0);

        canvasCaptura.toBlob((blob) => {
            blobCapturado = blob;
            imgPreview.src = URL.createObjectURL(blob);
            zonaCamara.classList.add("d-none");
            zonaPreview.classList.remove("d-none");
            if (streamCamara) {
                streamCamara.getTracks().forEach(t => t.stop());
                streamCamara = null;
            }
        }, "image/jpeg", 0.92);
    });

    // --- Opción: subir archivo ---
    btnUsarArchivo.addEventListener("click", () => {
        resetearVistas();
        inputArchivo.click();
    });

    inputArchivo.addEventListener("change", () => {
        const archivo = inputArchivo.files[0];
        if (!archivo) return;
        blobCapturado = archivo;
        imgPreview.src = URL.createObjectURL(archivo);
        zonaPreview.classList.remove("d-none");
    });

    // --- Opción: usar foto de perfil ---
    btnUsarPerfil.addEventListener("click", () => {
        resetearVistas();
        const urlFoto = obtenerUrlFotoPerfil();

        if (!urlFoto) {
            errorBox.textContent = "No tienes una foto de perfil registrada. Usa la cámara o sube una imagen.";
            errorBox.classList.add("visible");
            return;
        }

        usarPerfilSeleccionado = true;
        imgPreview.src = urlFoto;
        zonaPreview.classList.remove("d-none");
    });

    btnReintentar.addEventListener("click", resetearVistas);

    // --- Enviar al backend para análisis ---
    btnAnalizar.addEventListener("click", async () => {
        errorBox.classList.remove("visible");
        resultadoBox.classList.remove("visible");
        spinnerAnalisis.classList.add("visible");
        zonaPreview.classList.add("d-none");

        const formData = new FormData();
        if (usarPerfilSeleccionado) {
            formData.append("usar_perfil", "true");
        } else {
            if (!blobCapturado) {
                spinnerAnalisis.classList.remove("visible");
                errorBox.textContent = "No se detectó ninguna imagen para analizar.";
                errorBox.classList.add("visible");
                zonaPreview.classList.remove("d-none");
                return;
            }
            formData.append("imagen", blobCapturado, "captura.jpg");
        }

        try {
            const resp = await fetch(obtenerUrlAnalizar(), {
                method: "POST",
                headers: { "X-CSRFToken": obtenerCSRFToken() },
                body: formData
            });
            const data = await resp.json();
            spinnerAnalisis.classList.remove("visible");

            if (data.ok) {
                formaDetectada.textContent = data.forma;
                recomendacionTexto.textContent = data.recomendacion;

                if (metricasChips) {
                    const m = data.metricas;
                    metricasChips.innerHTML =
                        `Largo/Ancho: <span class="metrica-valor">${m.ratio_largo_ancho}</span> &nbsp;·&nbsp; ` +
                        `Mandíbula/Pómulo: <span class="metrica-valor">${m.ratio_mandibula_pomulo}</span> &nbsp;·&nbsp; ` +
                        `Frente/Pómulo: <span class="metrica-valor">${m.ratio_frente_pomulo}</span>`;
                }

                resultadoBox.classList.add("visible");
            } else {
                errorBox.textContent = data.error;
                errorBox.classList.add("visible");
                zonaPreview.classList.remove("d-none");
            }
        } catch (err) {
            spinnerAnalisis.classList.remove("visible");
            errorBox.textContent = "Error de conexión. Intenta nuevamente.";
            errorBox.classList.add("visible");
            zonaPreview.classList.remove("d-none");
        }
    });
});

/* ============================================================
   SISTEMA DE CALIFICACIONES Y RESEÑAS
   ============================================================ */
document.addEventListener("DOMContentLoaded", () => {
    const dataDiv = document.getElementById("calificacion-data");
    if (!dataDiv) return; // No hay sesión iniciada

    const URL_VERIFICAR = dataDiv.dataset.urlVerificar;
    const URL_GUARDAR = dataDiv.dataset.urlGuardar;
    const URL_OMITIR = dataDiv.dataset.urlOmitir;

    const modalEl = document.getElementById("calificacionModal");
    const modalCalificacion = new bootstrap.Modal(modalEl);

    const inputCitaId = document.getElementById("calificacionCitaId");
    const spanServicio = document.getElementById("calificacionServicio");
    const spanBarbero = document.getElementById("calificacionBarbero");
    const contenedorEstrellas = document.getElementById("estrellasCalificacion");
    const estrellas = contenedorEstrellas.querySelectorAll("i");
    const inputValor = document.getElementById("calificacionValor");
    const textareaComentario = document.getElementById("calificacionComentario");
    const divError = document.getElementById("calificacionError");
    const form = document.getElementById("formCalificacion");
    const btnEnviar = document.getElementById("btnEnviarCalificacion");
    const btnOmitir = document.getElementById("btnOmitirCalificacion");

    let calificacionEnviada = false; // true solo cuando el POST a guardar_calificacion fue exitoso

    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== "") {
            const cookies = document.cookie.split(";");
            for (let cookie of cookies) {
                cookie = cookie.trim();
                if (cookie.substring(0, name.length + 1) === (name + "=")) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    function pintarEstrellas(valor) {
        estrellas.forEach(estrella => {
            const v = parseInt(estrella.dataset.valor, 10);
            estrella.classList.toggle("bi-star-fill", v <= valor);
            estrella.classList.toggle("bi-star", v > valor);
            estrella.classList.toggle("activa", v <= valor);
        });
    }

    estrellas.forEach(estrella => {
        estrella.addEventListener("click", () => {
            const valor = parseInt(estrella.dataset.valor, 10);
            inputValor.value = valor;
            pintarEstrellas(valor);
            divError.style.display = "none";
        });
        estrella.addEventListener("mouseenter", () => {
            pintarEstrellas(parseInt(estrella.dataset.valor, 10));
        });
    });
    contenedorEstrellas.addEventListener("mouseleave", () => {
        pintarEstrellas(parseInt(inputValor.value || 0, 10));
    });

    async function verificarCalificacionPendiente() {
        try {
            const resp = await fetch(URL_VERIFICAR, { headers: { "X-Requested-With": "XMLHttpRequest" } });
            const data = await resp.json();

            if (data.pendiente) {
                inputCitaId.value = data.cita_id;
                spanServicio.textContent = data.servicio;
                spanBarbero.textContent = data.barbero;
                inputValor.value = "";
                pintarEstrellas(0);
                textareaComentario.value = "";
                divError.style.display = "none";
                calificacionEnviada = false;

                setTimeout(() => modalCalificacion.show(), 800);
            }
        } catch (e) {
            console.error("Error al verificar calificación pendiente:", e);
        }
    }
    verificarCalificacionPendiente();

    async function registrarOmision() {
        const citaId = inputCitaId.value;
        if (!citaId) return;

        try {
            await fetch(URL_OMITIR, {
                method: "POST",
                headers: {
                    "X-Requested-With": "XMLHttpRequest",
                    "X-CSRFToken": getCookie("csrftoken")
                },
                body: new URLSearchParams({ cita_id: citaId })
            });
        } catch (e) {
            console.error("No se pudo registrar la omisión de la calificación:", e);
        }
    }

    // Se dispara SIEMPRE que el modal se oculte: X, backdrop, Esc, botón Omitir, o hide() por JS
    modalEl.addEventListener("hide.bs.modal", () => {
        if (calificacionEnviada) return; // si ya calificó, no hay nada que "omitir"
        registrarOmision();
    });

    if (btnOmitir) {
        btnOmitir.addEventListener("click", () => modalCalificacion.hide());
    }

    form.addEventListener("submit", async (e) => {
        e.preventDefault();

        if (!inputValor.value) {
            divError.textContent = "Por favor selecciona una calificación en estrellas.";
            divError.style.display = "block";
            return;
        }

        btnEnviar.disabled = true;
        const textoOriginal = btnEnviar.innerHTML;
        btnEnviar.innerHTML = "Enviando...";

        const formData = new FormData(form);

        try {
            const resp = await fetch(URL_GUARDAR, {
                method: "POST",
                headers: {
                    "X-Requested-With": "XMLHttpRequest",
                    "X-CSRFToken": getCookie("csrftoken")
                },
                body: formData
            });
            const data = await resp.json();

            if (data.ok) {
                calificacionEnviada = true; // evita que hide.bs.modal la registre como omitida
                modalEl.querySelector(".modal-body").innerHTML = `
                    <div class="text-center py-4">
                        <i class="bi bi-check-circle-fill text-gold" style="font-size:3rem;"></i>
                        <p class="text-white fs-5 mt-3 mb-0">${data.mensaje}</p>
                    </div>`;
                modalEl.querySelector(".modal-footer").style.display = "none";
                setTimeout(() => modalCalificacion.hide(), 1800);
            } else {
                divError.textContent = data.error || "Ocurrió un error al enviar tu calificación.";
                divError.style.display = "block";
                btnEnviar.disabled = false;
                btnEnviar.innerHTML = textoOriginal;
            }
        } catch (err) {
            divError.textContent = "Error de conexión, intenta de nuevo.";
            divError.style.display = "block";
            btnEnviar.disabled = false;
            btnEnviar.innerHTML = textoOriginal;
        }
    });
});