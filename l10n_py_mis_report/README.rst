================================================================
Paraguay - Informes Contables MIS (Balance, ER, Flujo de Efectivo)
================================================================

Plantillas listas para `mis_builder` con la estructura del Plan de
Cuentas paraguayo (Resolución General N° 49/14):

* **Balance General** — Activo, Pasivo y Patrimonio Neto
* **Estado de Resultados** — Ingresos, Costos, Gastos y Resultado del Ejercicio
* **Flujo de Efectivo (Indirecto)** — apoyado en ``mis_builder_cash_flow``

Las fórmulas usan prefijos del Plan (``1.01.*``, ``2.01.*``, ``4.*``, etc.)
con ``balp[]`` / ``bale[]`` del MIS Builder.

Instalación
===========

Depende de ``l10n_py``, ``mis_builder`` y ``mis_builder_cash_flow``.
Al instalar, las plantillas quedan disponibles en
*Contabilidad → Informes → MIS Reports*.

Uso
===

#. Cree una instancia de informe desde *Configuración → MIS Builder
   → Instancias* eligiendo la plantilla deseada.
#. Configure el período y la empresa.
#. Genere el informe.

Créditos
========

* KMEE
