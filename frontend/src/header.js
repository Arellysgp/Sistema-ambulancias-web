document.addEventListener('DOMContentLoaded', () => {
    // 1. Buscamos el contenedor donde inyectaremos el header
    const headerContainer = document.getElementById('header-container');
    if (!headerContainer) return;

    // 2. Recuperamos el nombre del usuario de la memoria
    const nombreUsuario = localStorage.getItem('nombre_usuario') || 'Usuario';

    // 3. Construimos el HTML de la barra superior (El menú rojo)
    const headerHTML = `
        <nav class="navbar navbar-samu" role="navigation" aria-label="main navigation" style="background-color: #D0342C;">
            <div class="navbar-brand">
                <a class="navbar-item" href="#" style="color: white; font-weight: bold;">
                    🚑 SAMU <span style="font-weight: normal; margin-left: 10px; border-left: 1px solid rgba(255,255,255,0.3); padding-left: 10px; font-size: 0.9em;">Sistema de Atención Móvil de Urgencias</span>
                </a>
            </div>

            <div class="navbar-menu" style="background-color: transparent; box-shadow: none;">
                <div class="navbar-end">
                    <div class="navbar-item has-dropdown is-hoverable">
                        <a class="navbar-link" style="color: white;">
                            👤 ${nombreUsuario}
                        </a>
                        <div class="navbar-dropdown is-right" style="border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
                            <a class="navbar-item" onclick="cerrarSesion()">
                                🚪 Cerrar Sesión
                            </a>
                        </div>
                    </div>
                </div>
            </div>
        </nav>
    `;

    // 4. Inyectamos el HTML en la página
    headerContainer.innerHTML = headerHTML;
});

// Función global para cerrar sesión desde cualquier página
window.cerrarSesion = function() {
    // Borramos el nombre de la memoria del navegador
    localStorage.removeItem('nombre_usuario');
    
    // Redirigimos al index.html (saliendo de la carpeta 'pages' hacia la raíz)
    window.location.href = '../index.html'; 
};