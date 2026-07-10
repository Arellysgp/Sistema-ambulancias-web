// Variable globales para el mapa
let mapaConductor;
let marcadorIncidente;
let marcadorAmbulancia;
let rutaConductor;
let idEmergenciaActual = null;
let coordenadasRuta = [];
let intervaloAnimacion = null;

// Variables para la tabla
let listaEmergenciasCompleta = [];
let filtroActual = 'todas';
let paginaActual = 1;
const itemsPorPagina = 5;

const CONDUCTOR_API_URL = 'http://127.0.0.1:5000/api';

document.addEventListener('DOMContentLoaded', () => {
    iniciarMapa();
    buscarEmergenciaAsignada();
});

// 1. Inicializar el mapa de Leaflet
function iniciarMapa() {
    mapaConductor = L.map('mapa-conductor').setView([-12.0464, -77.0428], 12); // Centro en Lima

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap contributors'
    }).addTo(mapaConductor);
}

// 2. Buscar si hay una emergencia pendiente en la base de datos
function buscarEmergenciaAsignada() {
    fetch(`${CONDUCTOR_API_URL}/emergencias`)
        .then(response => response.json())
        .then(data => {
            // Guardamos todas las emergencias para la tabla
            listaEmergenciasCompleta = data;

            // Actualizamos la UI nueva
            actualizarResumenEmergencias();
            renderizarTablaEmergencias();
            configurarEventosTabla();

            // Buscamos la última emergencia que esté 'pendiente' o 'en_camino'
            const emergenciaActiva = data.find(e => e.estado === 'pendiente' || e.estado === 'en_camino');

            if (emergenciaActiva) {
                mostrarDetalles(emergenciaActiva);
            } else {
                // Si no hay emergencias, mostramos un mensaje de tranquilidad
                const alerta = document.getElementById('alerta-conductor');
                alerta.className = 'notification is-success is-light';
                alerta.innerHTML = '<i class="fa-solid fa-mug-hot"></i> No hay emergencias asignadas en este momento.';
            }
        })
        .catch(error => console.error("Error al conectar con el servidor:", error));
}

// 3. Llenar los datos en la pantalla y dibujar en el mapa
function mostrarDetalles(emergencia) {
    idEmergenciaActual = emergencia.id;
    // Llenar textos del HTML
    document.getElementById('cond-paciente').textContent = `${emergencia.nombre_paciente} (${emergencia.edad} años)`;
    document.getElementById('cond-direccion').textContent = `${emergencia.direccion}${emergencia.distrito ? ', ' + emergencia.distrito : ''}${emergencia.provincia ? ' (' + emergencia.provincia + ')' : ''}`;
    document.getElementById('cond-descripcion').textContent = emergencia.descripcion;

    // Ocultar el mensaje de "Buscando..." y mostrar los detalles y botones
    document.getElementById('alerta-conductor').classList.add('is-hidden');
    document.getElementById('detalles-emergencia').classList.remove('is-hidden');

    // Trazar en el mapa si hay coordenadas
    if (emergencia.latitud && emergencia.longitud) {
        const lat = parseFloat(emergencia.latitud);
        const lng = parseFloat(emergencia.longitud);

        // Pin rojo del accidente
        marcadorIncidente = L.marker([lat, lng]).addTo(mapaConductor)
            .bindPopup('<b>🚨 Lugar de la Emergencia</b>').openPopup();

        trazarRutaDesdeAmbulancia(lat, lng);
    }
}

// 4. Simular la posición de la ambulancia y trazar la ruta hacia el accidente
function trazarRutaDesdeAmbulancia(latDestino, lngDestino) {
    // Simulamos que la ambulancia está a unos kilómetros del accidente
    const latAmbulancia = latDestino + (Math.random() - 0.5) * 0.05;
    const lngAmbulancia = lngDestino + (Math.random() - 0.5) * 0.05;

    marcadorAmbulancia = L.circleMarker([latAmbulancia, lngAmbulancia], {
        color: '#ffffff', weight: 2, fillColor: '#1a73e8', fillOpacity: 1, radius: 8
    }).addTo(mapaConductor).bindPopup('<b>🚑 Tu ubicación actual</b>');

    // Usamos OSRM pidiendo RUTAS ALTERNATIVAS agregando (alternatives=true)
    const urlOSRM = `https://router.project-osrm.org/route/v1/driving/${lngAmbulancia},${latAmbulancia};${lngDestino},${latDestino}?overview=full&geometries=geojson&alternatives=true`;

    fetch(urlOSRM)
        .then(response => response.json())
        .then(data => {
            if (data.routes && data.routes.length > 0) {

                // RUTA 1: La principal (Simularemos que tiene tráfico pesado -> ROJO)
                const rutaRoja = data.routes[0].geometry.coordinates.map(coord => [coord[1], coord[0]]);
                const tiempoRojo = Math.round(data.routes[0].duration / 60) + 15; // Le sumamos 15 mins por "tráfico"
                const distRoja = (data.routes[0].distance / 1000).toFixed(1);

                // Hacemos la línea roja MÁS GRUESA (weight 10) para que actúe como una sombra visible debajo de la azul si se cruzan.
                L.polyline(rutaRoja, {
                    color: '#e11d48', weight: 10, opacity: 0.7
                }).addTo(mapaConductor).bindPopup(`
                    <div style="font-family: 'Inter', sans-serif; width: 280px; padding: 4px; color: #0f172a;">
                      <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 12px;">
                        <div style="width: 40px; height: 40px; border-radius: 50%; background: #fee2e2; display: flex; align-items: center; justify-content: center; font-size: 1.2rem; color: #ef4444; flex-shrink: 0;">
                          <i class="fa-solid fa-triangle-exclamation"></i>
                        </div>
                        <div>
                          <h4 style="margin: 0; font-size: 0.95rem; font-weight: 700; color: #0f172a;">Tráfico Lento</h4>
                          <p style="margin: 2px 0 0 0; font-size: 0.75rem; color: #64748b; line-height: 1.3;">Congestión vehicular detectada en esta vía principal.</p>
                        </div>
                      </div>
                      <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 6px; border-top: 1px solid #e2e8f0; border-bottom: 1px solid #e2e8f0; padding: 10px 0; margin-bottom: 12px; text-align: center;">
                        <div>
                          <span style="font-size: 0.7rem; color: #64748b; display: block; margin-bottom: 4px;"><i class="fa-regular fa-clock"></i> Tiempo</span>
                          <strong style="font-size: 0.85rem; color: #0f172a; font-weight: 700;">${tiempoRojo} min</strong>
                        </div>
                        <div style="border-left: 1px solid #e2e8f0; border-right: 1px solid #e2e8f0;">
                          <span style="font-size: 0.7rem; color: #64748b; display: block; margin-bottom: 4px;"><i class="fa-solid fa-route"></i> Distancia</span>
                          <strong style="font-size: 0.85rem; color: #0f172a; font-weight: 700;">${distRoja} km</strong>
                        </div>
                        <div>
                          <span style="font-size: 0.7rem; color: #64748b; display: block; margin-bottom: 4px;"><i class="fa-solid fa-car-burst"></i> Tráfico</span>
                          <strong style="font-size: 0.85rem; color: #ef4444; font-weight: 700;">Lento</strong>
                        </div>
                      </div>
                      <div style="display: flex; gap: 8px;">
                        <button onclick="window.abrirModalRuta('lento')" style="flex: 1; padding: 6px 10px; background: #fff; border: 1px solid #cbd5e1; border-radius: 6px; font-size: 0.75rem; font-weight: 600; color: #0f172a; cursor: pointer;">Ver detalles</button>
                        <button onclick="document.getElementById('btn-en-camino').click()" style="flex: 1; padding: 6px 10px; background: #ef4444; border: 1px solid #ef4444; border-radius: 6px; font-size: 0.75rem; font-weight: 600; color: #fff; cursor: pointer;">Seguir ruta</button>
                      </div>
                    </div>
                `);

                // RUTA 2: La alternativa recomendada (Sin tráfico -> AZUL)
                let rutaAzul;
                let tiempoAzul;
                let distAzul;

                if (data.routes.length > 1) {
                    rutaAzul = data.routes[1].geometry.coordinates.map(coord => [coord[1], coord[0]]);
                    tiempoAzul = Math.round(data.routes[1].duration / 60); // Tiempo real, sin tráfico
                    distAzul = (data.routes[1].distance / 1000).toFixed(1);
                } else {
                    rutaAzul = rutaRoja;
                    tiempoAzul = Math.round(data.routes[0].duration / 60);
                    distAzul = distRoja;
                }

                coordenadasRuta = rutaAzul;

                // La línea azul es más delgada (weight 5) para que no tape a la roja si van por la misma calle
                rutaConductor = L.polyline(rutaAzul, {
                    color: '#3b82f6', weight: 5, opacity: 1.0
                }).addTo(mapaConductor).bindPopup(`
                    <div style="font-family: 'Inter', sans-serif; width: 280px; padding: 4px; color: #0f172a;">
                      <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 12px;">
                        <div style="width: 40px; height: 40px; border-radius: 50%; background: #dbeafe; display: flex; align-items: center; justify-content: center; font-size: 1.2rem; color: #3b82f6; flex-shrink: 0;">
                          <i class="fa-solid fa-road"></i>
                        </div>
                        <div>
                          <h4 style="margin: 0; font-size: 0.95rem; font-weight: 700; color: #0f172a;">Ruta Recomendada</h4>
                          <p style="margin: 2px 0 0 0; font-size: 0.75rem; color: #64748b; line-height: 1.3;">SAMU sugiere esta vía para llegar al incidente.</p>
                        </div>
                      </div>
                      <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 6px; border-top: 1px solid #e2e8f0; border-bottom: 1px solid #e2e8f0; padding: 10px 0; margin-bottom: 12px; text-align: center;">
                        <div>
                          <span style="font-size: 0.7rem; color: #64748b; display: block; margin-bottom: 4px;"><i class="fa-regular fa-clock"></i> Tiempo</span>
                          <strong style="font-size: 0.85rem; color: #0f172a; font-weight: 700;">${tiempoAzul} min</strong>
                        </div>
                        <div style="border-left: 1px solid #e2e8f0; border-right: 1px solid #e2e8f0;">
                          <span style="font-size: 0.7rem; color: #64748b; display: block; margin-bottom: 4px;"><i class="fa-solid fa-route"></i> Distancia</span>
                          <strong style="font-size: 0.85rem; color: #0f172a; font-weight: 700;">${distAzul} km</strong>
                        </div>
                        <div>
                          <span style="font-size: 0.7rem; color: #64748b; display: block; margin-bottom: 4px;"><i class="fa-solid fa-car"></i> Tráfico</span>
                          <strong style="font-size: 0.85rem; color: #10b981; font-weight: 700;">Despejado</strong>
                        </div>
                      </div>
                      <div style="display: flex; gap: 8px;">
                        <button onclick="window.abrirModalRuta('rapido')" style="flex: 1; padding: 6px 10px; background: #fff; border: 1px solid #cbd5e1; border-radius: 6px; font-size: 0.75rem; font-weight: 600; color: #0f172a; cursor: pointer;">Ver detalles</button>
                        <button onclick="document.getElementById('btn-en-camino').click()" style="flex: 1; padding: 6px 10px; background: #3b82f6; border: 1px solid #3b82f6; border-radius: 6px; font-size: 0.75rem; font-weight: 600; color: #fff; cursor: pointer;">Seguir ruta</button>
                      </div>
                    </div>
                `).openPopup();

                // Ajustamos la cámara del mapa
                mapaConductor.fitBounds(rutaConductor.getBounds(), { padding: [50, 50] });

            } else {
                coordenadasRuta = [[latAmbulancia, lngAmbulancia], [latDestino, lngDestino]];
                rutaConductor = L.polyline(coordenadasRuta, { color: '#1a73e8', weight: 6 }).addTo(mapaConductor);
                mapaConductor.fitBounds(rutaConductor.getBounds());
            }
        })
        .catch(error => console.error("Error al trazar ruta con OSRM:", error));
}

// Función para que la computadora hable (Voz de GPS)
function hablarGPS(texto) {
    if ('speechSynthesis' in window) {
        window.speechSynthesis.cancel(); // Corta si estaba diciendo algo antes
        const mensaje = new SpeechSynthesisUtterance(texto);

        // TRUCO: Intentamos buscar una voz femenina más parecida a Waze
        const voces = window.speechSynthesis.getVoices();
        // Buscamos a "Google español", "Microsoft Sabina" o "Microsoft Helena"
        const vozWaze = voces.find(voz =>
            voz.lang.includes('es') && (voz.name.includes('Google') || voz.name.includes('Sabina') || voz.name.includes('Helena'))
        );

        if (vozWaze) {
            mensaje.voice = vozWaze;
        } else {
            mensaje.lang = 'es-ES'; // Fallback a cualquier voz en español
        }

        mensaje.rate = 1.0; // Velocidad calmada de locutora
        mensaje.pitch = 1.2; // Tono ligeramente más agudo para simular voz femenina estándar
        window.speechSynthesis.speak(mensaje);
    }
}

// Función para mover la ambulancia animadamente hacia el destino
function animarAmbulancia() {
    if (!coordenadasRuta || coordenadasRuta.length === 0) return;

    let pasoActual = 0;
    const totalPasos = coordenadasRuta.length;
    let dichoMitad = false;
    let dichoFinal = false;

    // Limpiamos cualquier animación previa
    if (intervaloAnimacion) clearInterval(intervaloAnimacion);

    // VOZ DE INICIO
    hablarGPS("Iniciando ruta. Conduzca con precaución. En 100 metros, gire a la derecha.");

    intervaloAnimacion = setInterval(() => {
        // VOZ AL MEDIO DEL CAMINO
        if (!dichoMitad && pasoActual === Math.floor(totalPasos * 0.5)) {
            hablarGPS("Continúe por esta vía. Tráfico ligero detectado.");
            dichoMitad = true;
        }

        // VOZ CASI AL LLEGAR
        if (!dichoFinal && pasoActual === Math.floor(totalPasos * 0.85)) {
            hablarGPS("El destino está a la derecha.");
            dichoFinal = true;
        }

        // Si ya llegó al final
        if (pasoActual >= totalPasos) {
            clearInterval(intervaloAnimacion);
            marcadorAmbulancia.bindPopup('<b>🚑 ¡Unidad en el lugar!</b>').openPopup();
            hablarGPS("Ha llegado a la emergencia. Por favor, asista al paciente.");
            if (rutaConductor) mapaConductor.removeLayer(rutaConductor); // Borra el último rastro
            return;
        }

        // 1. Movemos el circulito azul a la siguiente coordenada
        marcadorAmbulancia.setLatLng(coordenadasRuta[pasoActual]);

        // 2. Actualizamos la línea azul para que solo dibuje lo que falta recorrer
        if (rutaConductor) {
            rutaConductor.setLatLngs(coordenadasRuta.slice(pasoActual));
        }

        pasoActual++;
    }, 800);
}
// --- LÓGICA DE LOS BOTONES DEL CONDUCTOR ---

// Botón: En camino (Cambia a estado 'en_camino')
document.getElementById('btn-en-camino').addEventListener('click', () => {
    actualizarEstadoBaseDatos('en_camino', '¡Aviso enviado! En ruta hacia la emergencia.');
});

// Botón: Finalizar Atención (Cambia a estado 'cerrada')
document.getElementById('btn-finalizar').addEventListener('click', () => {
    actualizarEstadoBaseDatos('atendida', 'Atención finalizada con éxito. Unidad libre.');
});

// Función maestra que se comunica con Python
function actualizarEstadoBaseDatos(nuevoEstado, mensajeExito) {
    if (!idEmergenciaActual) return;

    const btnCamino = document.getElementById('btn-en-camino');
    const btnFinalizar = document.getElementById('btn-finalizar');

    // Apagamos para evitar doble clic mientras carga
    btnCamino.disabled = true;
    btnFinalizar.disabled = true;

    // Recuperamos el ID del conductor que inició sesión
    const conductorId = localStorage.getItem('user_id');

    fetch(`${CONDUCTOR_API_URL}/emergencias/${idEmergenciaActual}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            estado: nuevoEstado,
            conductor_id: conductorId
        })
    })
        .then(response => {
            if (response.ok) {
                if (nuevoEstado === 'en_camino') {
                    // Mantenemos el color amarillo opaco y cambiamos el texto
                    btnCamino.innerHTML = '<i class="fa-solid fa-truck-fast" style="margin-right: 8px;"></i> Ya estás en camino';

                    // Encendemos el botón de finalizar
                    btnFinalizar.disabled = false;

                    // 👇 MAGIA 2: Arrancamos la simulación de movimiento
                    animarAmbulancia();
                }
                else if (nuevoEstado === 'atendida') {
                    // Llenamos el modal con los datos actuales de la pantalla
                    document.getElementById('modal-paciente').textContent = document.getElementById('cond-paciente').textContent;
                    document.getElementById('modal-direccion').textContent = document.getElementById('cond-direccion').textContent;
                    document.getElementById('modal-detalle').textContent = document.getElementById('cond-descripcion').textContent;

                    // Formateamos la fecha y hora de finalización actual
                    const ahora = new Date();
                    const dia = String(ahora.getDate()).padStart(2, '0');
                    const mes = String(ahora.getMonth() + 1).padStart(2, '0');
                    const anio = ahora.getFullYear();
                    const hora = String(ahora.getHours()).padStart(2, '0');
                    const minutos = String(ahora.getMinutes()).padStart(2, '0');
                    document.getElementById('modal-hora').textContent = `${dia}/${mes}/${anio} - ${hora}:${minutos}`;

                    // Reiniciamos los botones de feedback
                    document.querySelectorAll('.feedback-btn').forEach(btn => btn.classList.remove('is-active'));

                    // Mostramos el modal
                    document.getElementById('modal-finalizar-atencion').classList.add('is-active');

                    // Guardamos el callback para cuando cierren el modal
                    window.finalizarAtencionCallback = () => {
                        document.getElementById('modal-finalizar-atencion').classList.remove('is-active');

                        // 👇 Apagamos el motor de animación al finalizar
                        if (intervaloAnimacion) clearInterval(intervaloAnimacion);

                        // Limpiamos pantalla
                        document.getElementById('detalles-emergencia').classList.add('is-hidden');
                        const alerta = document.getElementById('alerta-conductor');
                        alerta.classList.remove('is-hidden');
                        alerta.className = 'notification is-info is-light';
                        alerta.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Unidad libre. Buscando nueva asignación...';

                        if (rutaConductor) mapaConductor.removeLayer(rutaConductor);
                        if (marcadorIncidente) mapaConductor.removeLayer(marcadorIncidente);
                        idEmergenciaActual = null;

                        // Restauramos el botón a su texto original para la próxima emergencia
                        btnCamino.innerHTML = '<i class="fa-solid fa-truck-fast" style="margin-right: 8px;"></i> En camino';
                        btnCamino.disabled = false;
                        btnFinalizar.disabled = false;

                        // Llama a la siguiente emergencia al instante
                        buscarEmergenciaAsignada();
                    };
                }
            }
        })
        .catch(error => console.error("Error al actualizar:", error));
}

// Radar del conductor: Pregunta por nuevas emergencias cada 5 segundos
setInterval(() => {
    // Solo busca si no hay una emergencia asignada en este momento
    if (!idEmergenciaActual) {
        buscarEmergenciaAsignada();
    }
}, 5000);

// --- EVENTOS DEL MODAL DE FINALIZACIÓN (NUEVO) ---
document.addEventListener('DOMContentLoaded', () => {
    const modal = document.getElementById('modal-finalizar-atencion');
    const btnClose = document.getElementById('btn-close-modal-finalizar');
    const btnAceptar = document.getElementById('btn-modal-aceptar');
    const feedbackBtns = document.querySelectorAll('.feedback-btn');

    if (btnClose) {
        btnClose.addEventListener('click', () => {
            if (typeof window.finalizarAtencionCallback === 'function') {
                window.finalizarAtencionCallback();
            }
        });
    }

    if (btnAceptar) {
        btnAceptar.addEventListener('click', () => {
            if (typeof window.finalizarAtencionCallback === 'function') {
                window.finalizarAtencionCallback();
            }
        });
    }

    feedbackBtns.forEach(btn => {
        btn.addEventListener('click', function () {
            feedbackBtns.forEach(b => b.classList.remove('is-active'));
            this.classList.add('is-active');
            // Aquí se podría guardar el feedback si el backend lo soportara
            console.log("Feedback seleccionado:", this.getAttribute('data-rating'));
        });
    });
});

// --- NUEVAS FUNCIONES PARA LA INTERFAZ TAILWIND ---
function actualizarResumenEmergencias() {
    const total = listaEmergenciasCompleta.length;
    const pendientes = listaEmergenciasCompleta.filter(e => e.estado === 'pendiente').length;
    const enCamino = listaEmergenciasCompleta.filter(e => e.estado === 'en_camino').length;
    const atendidas = listaEmergenciasCompleta.filter(e => e.estado === 'finalizado').length;

    // Actualizar Panel Izquierdo
    const rTodas = document.getElementById('resumen-todas');
    const rPendientes = document.getElementById('resumen-pendientes');
    const rEnCamino = document.getElementById('resumen-encamino');
    const rAtendidas = document.getElementById('resumen-atendidas');
    if (rTodas) rTodas.textContent = total;
    if (rPendientes) rPendientes.textContent = pendientes;
    if (rEnCamino) rEnCamino.textContent = enCamino;
    if (rAtendidas) rAtendidas.textContent = atendidas;

    // Actualizar Pestañas de la Tabla
    const tTodas = document.getElementById('tab-todas');
    const tPendientes = document.getElementById('tab-pendientes');
    const tEnCamino = document.getElementById('tab-encamino');
    const tAtendidas = document.getElementById('tab-atendidas');
    if (tTodas) tTodas.textContent = total;
    if (tPendientes) tPendientes.textContent = pendientes;
    if (tEnCamino) tEnCamino.textContent = enCamino;
    if (tAtendidas) tAtendidas.textContent = atendidas;
}

function renderizarTablaEmergencias() {
    const tbody = document.getElementById('tabla-emergencias-conductor');
    if (!tbody) return;

    let filtradas = listaEmergenciasCompleta;

    // Aplicar filtro de pestañas
    if (filtroActual !== 'todas') {
        filtradas = filtradas.filter(e => e.estado === filtroActual);
    }

    // Aplicar filtro de buscador textual
    const inputBuscar = document.getElementById('input-buscar-emergencia');
    const query = inputBuscar ? inputBuscar.value.toLowerCase() : '';
    if (query) {
        filtradas = filtradas.filter(e =>
            e.nombre_paciente.toLowerCase().includes(query) ||
            e.direccion.toLowerCase().includes(query) ||
            e.descripcion.toLowerCase().includes(query)
        );
    }

    if (filtradas.length === 0) {
        tbody.innerHTML = `<tr><td colspan="7" class="text-center py-8 text-gray-500 font-medium">No se encontraron emergencias</td></tr>`;
        renderizarPaginacion(0);
        return;
    }

    // Lógica de Paginación
    const startIndex = (paginaActual - 1) * itemsPorPagina;
    const endIndex = startIndex + itemsPorPagina;
    const paginadas = filtradas.slice(startIndex, endIndex);

    let html = '';
    paginadas.forEach((e, index) => {
        const rowBg = index % 2 === 0 ? 'bg-white' : 'bg-gray-50/30';
        const globalIndex = startIndex + index + 1;
        html += `
        <tr class="${rowBg} hover:bg-gray-50 transition-colors">
            <td class="px-4 py-3 whitespace-nowrap text-sm font-medium text-gray-900">${globalIndex}</td>
            <td class="px-4 py-3 whitespace-nowrap">
                <div class="text-sm font-medium text-gray-900">${e.nombre_paciente}</div>
                <div class="text-xs text-gray-500">${e.edad || '?'} años</div>
            </td>
            <td class="px-4 py-3 whitespace-nowrap text-sm text-gray-700 truncate max-w-[200px]" title="${e.direccion}">${e.direccion}</td>
            <td class="px-4 py-3 text-sm text-gray-700 truncate max-w-[200px]" title="${e.descripcion}">${e.descripcion}</td>
            <td class="px-4 py-3 whitespace-nowrap">${getBadgeTailwind(e.estado)}</td>
            <td class="px-4 py-3 whitespace-nowrap text-sm text-gray-600">${formatearHora(e.fecha_registro)}</td>
            <td class="px-4 py-3 whitespace-nowrap text-center text-sm font-medium">
                <button onclick="window.verDetalleSeguro(${e.id})" class="text-indigo-600 hover:text-indigo-900 mr-3 transition-colors" title="Ver detalles">
                    <i class="fa-regular fa-eye"></i>
                </button>
                <button class="text-gray-400 hover:text-gray-600 transition-colors cursor-not-allowed" title="Ubicación en mapa (No disponible en esta vista)">
                    <i class="fa-solid fa-map-location-dot"></i>
                </button>
            </td>
        </tr>`;
    });
    tbody.innerHTML = html;

    renderizarPaginacion(filtradas.length);
}

function getBadgeTailwind(estado) {
    switch (estado) {
        case 'pendiente':
            return '<span class="px-2.5 py-1 inline-flex text-xs leading-5 font-semibold rounded-full bg-orange-100 text-orange-800 border border-orange-200">Pendiente</span>';
        case 'en_camino':
            return '<span class="px-2.5 py-1 inline-flex text-xs leading-5 font-semibold rounded-full bg-blue-100 text-blue-800 border border-blue-200"><i class="fa-solid fa-car text-[10px] mr-1 mt-[2px]"></i> En camino</span>';
        case 'finalizado':
            return '<span class="px-2.5 py-1 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800 border border-green-200"><i class="fa-solid fa-check text-[10px] mr-1 mt-[2px]"></i> Atendida</span>';
        default:
            return `<span class="px-2.5 py-1 inline-flex text-xs leading-5 font-semibold rounded-full bg-gray-100 text-gray-800 border border-gray-200">${estado}</span>`;
    }
}

function formatearHora(fechaStr) {
    if (!fechaStr) return '--:--';
    const date = new Date(fechaStr);
    let h = date.getHours();
    let m = date.getMinutes();
    const ampm = h >= 12 ? 'PM' : 'AM';
    h = h % 12;
    h = h ? h : 12;
    m = m < 10 ? '0' + m : m;
    return `${h}:${m} ${ampm}`;
}

function configurarEventosTabla() {
    // Evento para el buscador
    const inputBuscar = document.getElementById('input-buscar-emergencia');
    if (inputBuscar) {
        inputBuscar.addEventListener('input', () => {
            paginaActual = 1;
            renderizarTablaEmergencias();
        });
    }

    // Eventos para las pestañas
    const tabs = document.querySelectorAll('.tab-filtro');
    tabs.forEach(tab => {
        tab.addEventListener('click', function () {
            // Quitar clases activas de todas las pestañas
            tabs.forEach(t => {
                t.classList.remove('border-gray-900', 'text-gray-900');
                t.classList.add('border-transparent', 'text-gray-500');
            });
            // Añadir activa a la clickeada
            this.classList.remove('border-transparent', 'text-gray-500');
            this.classList.add('border-gray-900', 'text-gray-900');

            filtroActual = this.getAttribute('data-filter');
            paginaActual = 1;
            renderizarTablaEmergencias();
        });
    });
}

function renderizarPaginacion(totalItems) {
    const container = document.getElementById('paginacion-conductor');
    if (!container) return;

    if (totalItems <= itemsPorPagina) {
        container.innerHTML = '';
        return;
    }

    const totalPages = Math.ceil(totalItems / itemsPorPagina);

    let html = `<nav class="relative z-0 inline-flex rounded-md shadow-sm -space-x-px" aria-label="Pagination">`;

    // Botón Anterior
    const prevDisabled = paginaActual === 1;
    html += `
      <a href="javascript:void(0)" onclick="${prevDisabled ? '' : `window.cambiarPagina(${paginaActual - 1})`}" 
         class="relative inline-flex items-center px-2 py-2 rounded-l-md border border-gray-300 bg-white text-sm font-medium ${prevDisabled ? 'text-gray-300 cursor-not-allowed' : 'text-gray-500 hover:bg-gray-50'}">
        <span class="sr-only">Anterior</span>
        <i class="fa-solid fa-chevron-left text-xs"></i>
      </a>
    `;

    // Botones de Páginas
    for (let i = 1; i <= totalPages; i++) {
        if (i === paginaActual) {
            html += `<a href="javascript:void(0)" class="relative inline-flex items-center px-4 py-2 border border-indigo-500 bg-gray-50 text-sm font-medium text-gray-900 z-10">${i}</a>`;
        } else {
            html += `<a href="javascript:void(0)" onclick="window.cambiarPagina(${i})" class="relative inline-flex items-center px-4 py-2 border border-gray-300 bg-white text-sm font-medium text-gray-700 hover:bg-gray-50">${i}</a>`;
        }
    }

    // Botón Siguiente
    const nextDisabled = paginaActual === totalPages;
    html += `
      <a href="javascript:void(0)" onclick="${nextDisabled ? '' : `window.cambiarPagina(${paginaActual + 1})`}" 
         class="relative inline-flex items-center px-2 py-2 rounded-r-md border border-gray-300 bg-white text-sm font-medium ${nextDisabled ? 'text-gray-300 cursor-not-allowed' : 'text-gray-500 hover:bg-gray-50'}">
        <span class="sr-only">Siguiente</span>
        <i class="fa-solid fa-chevron-right text-xs"></i>
      </a>
    </nav>`;

    container.innerHTML = html;
}

window.cambiarPagina = function (pagina) {
    paginaActual = pagina;
    renderizarTablaEmergencias();
};

window.verDetalleSeguro = function (id) {
    const emergencia = listaEmergenciasCompleta.find(e => e.id === id);
    if (!emergencia) return;

    const isAssignedToMe = String(emergencia.conductor_id) === String(USER_ID);

    if (isAssignedToMe) {
        // Mostrar alerta de asignación primero
        window.emergenciaAsignadaId = id;
        document.getElementById('modal-alerta-asignacion').classList.remove('hidden');
    } else {
        // Mostrar detalles directamente (como solo lectura)
        abrirModalDetalle(emergencia, false);
    }
};

window.aceptarAsignacion = function() {
    document.getElementById('modal-alerta-asignacion').classList.add('hidden');
    const emergencia = listaEmergenciasCompleta.find(e => e.id === window.emergenciaAsignadaId);
    if (emergencia) {
        abrirModalDetalle(emergencia, true);
        // Además de abrir el modal de detalle, podemos mostrar la ruta en el panel principal
        mostrarDetalles(emergencia);
    }
};

window.cerrarModalAsignacion = function() {
    document.getElementById('modal-alerta-asignacion').classList.add('hidden');
};

function abrirModalDetalle(emergencia, isAssignedToMe) {
    // 1. Poblado de datos en el modal
    document.getElementById('md-id-emergencia').textContent = 'EMG-' + String(emergencia.id).padStart(4, '0');

    // Badge de estado usando la función existente
    document.getElementById('md-estado-badge').innerHTML = getBadgeTailwind(emergencia.estado);

    // Info del Paciente
    document.getElementById('md-nombre').textContent = emergencia.nombre_paciente || 'Desconocido';
    document.getElementById('md-edad').textContent = emergencia.edad ? `${emergencia.edad} años` : 'No especificada';
    document.getElementById('md-telefono').textContent = emergencia.telefono || 'No registrado';

    // Ubicación
    document.getElementById('md-direccion').textContent = emergencia.direccion || 'No especificada';

    // Detalle
    document.getElementById('md-descripcion').textContent = emergencia.descripcion || 'Sin detalles';
    document.getElementById('md-fecha').textContent = formatearHora(emergencia.fecha_registro);

    // Adicional
    document.getElementById('md-unidad').textContent = `Unidad del Conductor #${emergencia.conductor_id || 'Sin Asignar'}`;
    document.getElementById('md-conductor').textContent = isAssignedToMe ? '¡Tú (Asignado)!' : (emergencia.conductor_id ? 'Asignado a otra unidad' : 'Sin asignar aún');

    // 2. Mostrar el modal (quitar hidden)
    const modal = document.getElementById('modal-detalle-emergencia');
    if (modal) {
        modal.classList.remove('hidden');
    }
}

window.cerrarModalDetalle = function() {
    const modal = document.getElementById('modal-detalle-emergencia');
    if (modal) {
        modal.classList.add('hidden');
    }
};

window.abrirModalRuta = function(tipo) {
    const modal = document.getElementById('modal-info-ruta');
    if (!modal) return;
    
    const titulo = document.getElementById('mr-titulo');
    const mensaje = document.getElementById('mr-mensaje');
    const iconContainer = document.getElementById('mr-icon-bg');
    const icon = document.getElementById('mr-icon');
    
    if (tipo === 'lento') {
        titulo.textContent = 'Ruta con Tráfico';
        mensaje.textContent = 'Esta ruta alternativa presenta demoras considerables debido a congestión vehicular en las avenidas principales. Evite transitar por esta zona si es posible.';
        iconContainer.className = 'mx-auto flex h-12 w-12 shrink-0 items-center justify-center rounded-full sm:mx-0 sm:h-10 sm:w-10 bg-red-100';
        icon.className = 'fa-solid fa-triangle-exclamation text-xl text-red-600';
    } else {
        titulo.textContent = 'Ruta Recomendada';
        mensaje.textContent = 'Esta es la vía más rápida calculada por el sistema en base al flujo vehicular actual. Se recomienda seguir este trazado para llegar a la emergencia a tiempo.';
        iconContainer.className = 'mx-auto flex h-12 w-12 shrink-0 items-center justify-center rounded-full sm:mx-0 sm:h-10 sm:w-10 bg-blue-100';
        icon.className = 'fa-solid fa-road text-xl text-blue-600';
    }
    
    modal.classList.remove('hidden');
};

window.cerrarModalRuta = function() {
    const modal = document.getElementById('modal-info-ruta');
    if (modal) modal.classList.add('hidden');
};