document.addEventListener('DOMContentLoaded', () => {
    // 1. Buscamos el contenedor donde inyectaremos el header
    const headerContainer = document.getElementById('header-container');
    if (!headerContainer) return;

    // 2. Recuperamos el nombre del usuario de la memoria
    const nombreUsuario = localStorage.getItem('nombre_usuario') || 'Usuario';

    // 3. Construimos el HTML de la barra superior (El menú oscuro premium)
    const headerHTML = `
        <style>
            .navbar-samu .navbar-item.has-dropdown:hover .navbar-link,
            .navbar-samu .navbar-link:hover { background-color: transparent !important; }
            .navbar-samu .navbar-dropdown {
                opacity: 0; transform: translateY(-10px); display: block !important; visibility: hidden; transition: all 0.3s ease; pointer-events: none; margin-top: 0 !important;
            }
            .navbar-samu .navbar-item.has-dropdown:hover .navbar-dropdown {
                opacity: 1; transform: translateY(0); visibility: visible; pointer-events: auto;
            }
            .navbar-samu .badge-user { transition: all 0.3s ease; }
            .navbar-samu .navbar-item.has-dropdown:hover .badge-user { background-color: #334155 !important; border-color: #475569 !important; }
                        /* Forzar que el menú y el perfil siempre se vean en celulares */
            @media (max-width: 1024px) {
                .navbar-samu {
                    display: flex !important;
                    align-items: center !important;
                    justify-content: space-between !important;
                    
                }
                .navbar-samu .navbar-brand {
                    flex-shrink: 1;
                    min-width: 0;
                }
                .navbar-samu .navbar-brand .navbar-item span {
                    display: none; /* Oculta el texto largo "Sistema de Atención..." en celulares para hacer espacio */
                }
                .navbar-samu .navbar-menu {
                    display: flex !important;
                    background: transparent !important;
                    box-shadow: none !important;
                    padding: 0 !important;
                }
                .navbar-samu .navbar-end {
                    justify-content: flex-end !important;
                    margin-left: auto !important;
                }
                .navbar-samu .badge-user {
                    padding: 4px 8px !important;
                    font-size: 0.75rem;
                }
                /* Arreglar el cuadro que se despliega para que no se salga de la pantalla */
                .navbar-samu .navbar-dropdown {
                    right: 0 !important;
                    left: auto !important;
                }
            }

        </style>
        <nav class="navbar navbar-samu" role="navigation" aria-label="main navigation" style="background-color: #0f172a; border-bottom: 1px solid #1e293b; min-height: 60px;">
            <div class="navbar-brand">
                <a class="navbar-item" href="#" style="color: white; font-weight: 700; display: flex; align-items: center; gap: 8px; font-size: 1.1rem; padding-left: 1.5rem; background-color: transparent !important;">
                    <i class="fa-solid fa-truck-medical" style="color: #ef4444; font-size: 1.3rem;"></i>
                    SAMU 
                    <span style="font-weight: 400; margin-left: 10px; border-left: 1px solid rgba(255,255,255,0.15); padding-left: 12px; font-size: 0.8em; color: #94a3b8; letter-spacing: 0.02em;">Sistema de Atención Móvil de Urgencias</span>
                </a>
            </div>

            <div class="navbar-menu" style="background-color: transparent; box-shadow: none;">
                <div class="navbar-end" style="padding-right: 1rem;">
                    <div class="navbar-item has-dropdown is-hoverable">
                        <a class="navbar-link" style="color: #f8fafc; font-family: 'JetBrains Mono', monospace; font-size: 0.8rem; font-weight: 600; letter-spacing: 0.03em; background-color: transparent !important;">
                            <span class="badge-user" style="background-color: #1e293b; padding: 6px 12px; border-radius: 6px; border: 1px solid #334155; display: flex; align-items: center; gap: 8px;">
                                <i class="fa-solid fa-user-shield" style="color: #94a3b8;"></i>
                                ${nombreUsuario}
                            </span>
                        </a>
                        <div class="navbar-dropdown is-right" style="background-color: #1e293b; border: 1px solid #334155; border-radius: 8px; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.3); padding: 0.5rem 0;">
                            <a class="navbar-item" onclick="mostrarModalLogout()" style="color: #f8fafc; transition: all 0.2s; font-size: 0.9rem;" onmouseover="this.style.backgroundColor='#334155'; this.style.color='#fca5a5';" onmouseout="this.style.backgroundColor='transparent'; this.style.color='#f8fafc';">
                                <i class="fa-solid fa-arrow-right-from-bracket" style="color: #ef4444; margin-right: 8px;"></i> Cerrar Sesión
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
window.ejecutarLogout = function () {
    // Borramos el nombre de la memoria del navegador
    localStorage.removeItem('nombre_usuario');

    // Redirigimos al index.html (saliendo de la carpeta 'pages' hacia la raíz)
    window.location.href = '../index.html';
};

// ── INJECT LOGOUT MODAL ──
function mostrarModalLogout() {
    if (!document.getElementById('modal-logout-global')) {
        const modalHTML = `
    <style>
      #modal-logout-global { display: none; position: fixed; inset: 0; background: rgba(15, 23, 42, 0.6); z-index: 999999; align-items: center; justify-content: center; backdrop-filter: blur(4px); font-family: 'Inter', sans-serif; }
      #modal-logout-global.open { display: flex; animation: fadeIn 0.2s ease; }
      .ml-box { background: #fff; border-radius: 16px; padding: 2.5rem 2rem; width: 100%; max-width: 400px; text-align: center; position: relative; box-shadow: 0 20px 25px -5px rgba(0,0,0,0.1); }
      .ml-close { position: absolute; top: 1rem; right: 1rem; background: none; border: none; font-size: 1.25rem; color: #64748b; cursor: pointer; transition: color 0.2s; }
      .ml-close:hover { color: #0f172a; }
      .ml-icon { width: 80px; height: 80px; border-radius: 50%; border: 2px solid #e2e8f0; display: flex; align-items: center; justify-content: center; font-size: 2.5rem; color: #475569; margin: 0 auto 1.5rem; }
      .ml-title { font-size: 1.25rem; font-weight: 600; color: #0f172a; margin-bottom: 0.75rem; }
      .ml-text { font-size: 0.875rem; color: #64748b; margin-bottom: 2rem; line-height: 1.5; }
      .ml-actions { display: flex; gap: 1rem; justify-content: center; }
      .btn-ml-cancel { flex: 1; padding: 0.75rem; background: #fff; border: 1px solid #cbd5e1; border-radius: 8px; font-weight: 500; color: #0f172a; cursor: pointer; transition: all 0.2s; font-family: 'Inter', sans-serif; }
      .btn-ml-cancel:hover { background: #f8fafc; border-color: #94a3b8; }
      .btn-ml-confirm { flex: 1; padding: 0.75rem; background: #475569; border: 1px solid #475569; border-radius: 8px; font-weight: 500; color: #fff; cursor: pointer; transition: all 0.2s; font-family: 'Inter', sans-serif; }
      .btn-ml-confirm:hover { background: #334155; }
    </style>
    <div id="modal-logout-global">
      <div class="ml-box">
        <button class="ml-close" onclick="document.getElementById('modal-logout-global').classList.remove('open')">✕</button>
        <div class="ml-icon"><i class="fa-solid fa-arrow-right-from-bracket"></i></div>
        <div class="ml-title">¿Seguro que deseas cerrar sesión?</div>
        <div class="ml-text">Vas a cerrar tu sesión actual.<br>Podrás iniciar sesión nuevamente cuando lo desees.</div>
        <div class="ml-actions">
          <button class="btn-ml-cancel" onclick="document.getElementById('modal-logout-global').classList.remove('open')">Cancelar</button>
          <button class="btn-ml-confirm" onclick="ejecutarLogout()">Sí, cerrar sesión</button>
        </div>
      </div>
    </div>
    `;
        document.body.insertAdjacentHTML('beforeend', modalHTML);
        // Include FontAwesome if missing
        if (!document.querySelector('link[href*="font-awesome"]')) {
            document.head.insertAdjacentHTML('beforeend', '<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css"/>');
        }
    }
    document.getElementById('modal-logout-global').classList.add('open');
}
