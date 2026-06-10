---
name: claude-mem
description: Sistema de compresión de memoria persistente para mantener contexto entre sesiones mediante resúmenes semánticos.
---

# 🧠 Claude-Mem

Sistema de memoria persistente para agentes.

## Propósito
Preservar contexto a través de sesiones capturando observaciones de herramientas, generando resúmenes semánticos y haciéndolos disponibles en sesiones futuras.

## Cómo funciona
1. **Captura**: Observa el uso de herramientas y resultados.
2. **Resumen**: Genera una representación comprimida del conocimiento adquirido.
3. **Persistencia**: Guarda la memoria en el sistema de archivos.
4. **Recuperación**: Permite al agente buscar conocimientos previos al iniciar nuevas tareas.

## Uso por el Agente
- Consultar memorias previas al iniciar una fase.
- Guardar hitos importantes al finalizar tareas.
- Evitar repetición de errores documentando "lecciones aprendidas" automáticamente.

---
*Referencia: https://github.com/thedotmack/claude-mem*
