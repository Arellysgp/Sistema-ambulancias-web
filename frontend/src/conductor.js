// Variable globales para el mapa
let mapaConductor;
let marcadorIncidente;
let marcadorAmbulancia;
let rutaConductor;
let idEmergenciaActual = null; 
let coordenadasRuta = [];       
let intervaloAnimacion = null;  

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

    // Usamos OSRM para trazar la línea de la ruta
    const urlOSRM = `https://router.project-osrm.org/route/v1/driving/${lngAmbulancia},${latAmbulancia};${lngDestino},${latDestino}?overview=full&geometries=geojson`;

    // Usamos OSRM para trazar la línea de la ruta
    fetch(urlOSRM)
        .then(response => response.json())
        .then(data => {
            if (data.routes && data.routes.length > 0) {
                // 👇 MAGIA 1: Guardamos todas las coordenadas de la ruta aquí
                coordenadasRuta = data.routes[0].geometry.coordinates.map(coord => [coord[1], coord[0]]);
            } else {
                // Fallback: Línea recta si OSRM no encuentra ruta (por estar en el mar o cerro)
                coordenadasRuta = [
                    [latAmbulancia, lngAmbulancia],
                    [(latAmbulancia + latDestino)/2, (lngAmbulancia + lngDestino)/2],
                    [latDestino, lngDestino]
                ];
            }
            
            rutaConductor = L.polyline(coordenadasRuta, { 
                color: '#1a73e8', weight: 6, opacity: 0.8 
            }).addTo(mapaConductor);

            // Ajustamos la cámara del mapa para que se vea toda la ruta
            mapaConductor.fitBounds(rutaConductor.getBounds());
        })
        .catch(error => {
            console.error("Error al trazar ruta con OSRM:", error);
            // Fallback: Línea recta
            coordenadasRuta = [
                [latAmbulancia, lngAmbulancia],
                [(latAmbulancia + latDestino)/2, (lngAmbulancia + lngDestino)/2],
                [latDestino, lngDestino]
            ];
            rutaConductor = L.polyline(coordenadasRuta, { color: '#1a73e8', weight: 6, opacity: 0.8 }).addTo(mapaConductor);
            mapaConductor.fitBounds(rutaConductor.getBounds());
        });
}

// Función para mover la ambulancia animadamente hacia el destino
function animarAmbulancia() {
    if (!coordenadasRuta || coordenadasRuta.length === 0) return;

    let pasoActual = 0;
    
    // Limpiamos cualquier animación previa por si acaso
    if (intervaloAnimacion) clearInterval(intervaloAnimacion);

    intervaloAnimacion = setInterval(() => {
        // Si ya llegó al final, detenemos el motor y borramos lo que quede de línea
        if (pasoActual >= coordenadasRuta.length) {
            clearInterval(intervaloAnimacion);
            marcadorAmbulancia.bindPopup('<b>🚑 ¡Unidad en el lugar!</b>').openPopup();
            if (rutaConductor) mapaConductor.removeLayer(rutaConductor); // Borra el último rastro
            return;
        }

        // 1. Movemos el circulito azul a la siguiente coordenada
        marcadorAmbulancia.setLatLng(coordenadasRuta[pasoActual]);

        // 👇 LA MAGIA: Actualizamos la línea azul para que solo dibuje lo que falta recorrer
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
        btn.addEventListener('click', function() {
            feedbackBtns.forEach(b => b.classList.remove('is-active'));
            this.classList.add('is-active');
            // Aquí se podría guardar el feedback si el backend lo soportara
            console.log("Feedback seleccionado:", this.getAttribute('data-rating'));
        });
    });
});