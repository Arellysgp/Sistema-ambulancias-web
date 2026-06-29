-- Migración 001: columnas activo + rol, y admin único
--  Ya ejecutado en Supabase. Este archivo es solo registro histórico para Git.

-- 1. Agregar columna 'activo' a la tabla usuarios
ALTER TABLE public.usuarios
ADD COLUMN IF NOT EXISTS activo BOOLEAN DEFAULT TRUE;

-- 2. Agregar columna 'rol' si no existe
ALTER TABLE public.usuarios
ADD COLUMN IF NOT EXISTS rol VARCHAR(50) DEFAULT 'operador';

-- 3. Admin único: favio@ambulancias.pe (id 12, ya existe en Supabase)
-- El admin duplicado admin@samu.pe fue eliminado con:
-- DELETE FROM public.usuarios WHERE email = 'admin@samu.pe';

-- Si en otro entorno se necesita recrear el admin, ejecutar:
-- UPDATE public.usuarios SET rol = 'admin', activo = TRUE
-- WHERE email = 'favio@ambulancias.pe';