# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-06-10
### Added
- **Arquitectura Base (Fase 1)**: Estructura modular separando la lógica del núcleo (`.ats_core`) del usuario.
- **Mapeo Condicional (`EnvManager.psm1`)**: Sistema que inyecta variables de entorno en memoria para Siemens NX basado en la existencia de directorios. Soporta configuraciones modulares (CAD/CAM/Templates/etc).
- **Escáner de Registro (`RegistryScanner.psm1`)**: Lógica para extraer automáticamente la ruta de instalación de Siemens NX desde `HKLM:\SOFTWARE\Siemens\NX`, con soporte para sobreescritura (override).
- **UI y Lanzador (`Start-NXLauncher.ps1`, `AtsUi.psm1`)**: Interfaz CLI interactiva con estética de ATS Global para seleccionar versiones de NX cuando hay múltiples configuraciones disponibles.
- **Configuración de Red (`ConfigLoader.psm1`)**: Soporte para instalaciones centralizadas con un asistente inicial de primera ejecución que guarda la selección predeterminada para todos los usuarios en `global.config`.
- Punto de entrada principal en batch (`Run-ATSLauncher.bat`) que facilita el lanzamiento del script de PowerShell evitando bloqueos de políticas de ejecución.
- Plantilla base de directorios y configuración JSON (`TEMPLATE.config`) para nuevas integraciones de clientes.
