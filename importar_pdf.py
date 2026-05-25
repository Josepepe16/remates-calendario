"""
Script de importacion de remates desde el PDF.
Ejecutar una sola vez: python importar_pdf.py
"""
import sqlite3
import os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.environ.get('REMATES_DATA_DIR', BASE_DIR)
DB_PATH = os.path.join(DATA_DIR, 'remates.db')

now = datetime.now().isoformat()

# (titulo, fecha_remate, lugar, notas)
# Hora incluida en fecha cuando era legible en el PDF.
# "Mercado" en lugar = tipo de remate segun el PDF.
# Las notas incluyen informacion de transmision y telefono del PDF.

REMATES = [
    # ── JUNIO 2026 ──────────────────────────────────────────────────────────
    (
        "Recuperacion — Gran Reserva",
        "2026-06-07",
        None,
        "PDF: Miercoles 7. Datos a completar."
    ),
    (
        "Lote 21",
        "2026-06-08",
        "Mercado",
        "PDF: Jueves 8 y Viernes 9. Datos a completar."
    ),
    (
        "Don Latorre",
        "2026-06-11T07:30",
        "Mercado",
        "PDF: Lunes 11. QRC — PAISA. Hora: 07:30. Tel: 072 335."
    ),
    (
        "Caballos de Raza",
        "2026-06-12",
        None,
        "PDF: Jueves 12. Datos a completar."
    ),
    (
        "Colonia de Vacaciones",
        "2026-06-19T13:30",
        "Mercado",
        "PDF: Jueves 19. PAISA. Hora: 13:30. Tel: 072 335."
    ),
    (
        "Lote 21",
        "2026-06-23",
        "Mercado",
        "PDF: Martes 23 y Miercoles 24. Datos a completar."
    ),

    # ── JULIO 2026 ───────────────────────────────────────────────────────────
    (
        "Mercado julio (nombre a completar)",
        "2026-07-08T10:30",
        "Mercado",
        "PDF: Miercoles 8. Nombre no legible. PAISA. Hora: 10:30. Tel: 072 315."
    ),
    (
        "Abraje de Servicios",
        "2026-07-15",
        None,
        "PDF: 15/7. Datos a completar."
    ),
    (
        "Lote 21",
        "2026-07-15",
        "Mercado",
        "PDF: Miercoles 15. Datos a completar."
    ),

    # ── AGOSTO 2026 ──────────────────────────────────────────────────────────
    (
        "Agosto mercado (nombre a completar)",
        "2026-08-01",
        "Mercado",
        "PDF: inicio agosto, nombre no legible. Tel: 072 305. Fecha aproximada."
    ),
    (
        "Nalez",
        "2026-08-04",
        None,
        "PDF: 4/8. Datos a completar."
    ),
    (
        "Mercado — agosto",
        "2026-08-06",
        "Mercado",
        "PDF: Miercoles 6. Datos a completar."
    ),
    (
        "Lote 21",
        "2026-08-13",
        "Mercado",
        "PDF: Miercoles 13 y Jueves 14. Datos a completar."
    ),
    (
        "Madres Nuevas",
        "2026-08-27",
        None,
        "PDF: 27/8. Datos a completar."
    ),

    # ── SETIEMBRE 2026 ───────────────────────────────────────────────────────
    (
        "Neo Perez",
        "2026-09-05",
        None,
        "PDF: 5/9. Datos a completar."
    ),
    (
        "Prendi",
        "2026-09-11",
        None,
        "PDF: 11 al 20 de setiembre. Datos a completar."
    ),
    (
        "Exposicion (fecha a confirmar)",
        "2026-09-09",
        None,
        "PDF: fecha a confirmar. Datos a completar."
    ),
    (
        "CDEL Gustavo Prendi",
        "2026-09-16",
        "Mercado",
        "PDF: Miercoles 16 y Jueves 17. Datos a completar."
    ),

    # ── OCTUBRE 2026 ─────────────────────────────────────────────────────────
    (
        "Nacional de 4S",
        "2026-10-09",
        None,
        "PDF: Sabado 9. Datos a completar."
    ),
    (
        "Lote 21",
        "2026-10-01",
        "Mercado",
        "PDF: Jueves — inicio octubre. Verificar fecha exacta."
    ),
    (
        "Expl San Jose",
        "2026-10-06",
        "Mercado",
        "PDF: Lunes 6. Tel: 1450 1396 / 149 572 + comision."
    ),
    (
        "Pasturas (a confirmar)",
        "2026-10-17",
        None,
        "PDF: Viernes 17 — fecha a confirmar desde el dia 4. Datos a completar."
    ),
    (
        "Especial Hembras Maldonado",
        "2026-10-21",
        "Mercado",
        "PDF: Jueves 21 al ~29. Datos a completar."
    ),

    # ── NOVIEMBRE 2026 ───────────────────────────────────────────────────────
    (
        "Sale (noviembre)",
        "2026-11-05",
        "Mercado",
        "PDF: Miercoles 5. Tel: 072 215. Nombre completo a confirmar."
    ),
    (
        "Noviembre mercado (nombre a completar)",
        "2026-11-03",
        "Mercado",
        "PDF: Lunes 3. ESTELA 20:30. Tel: 072 212. Nombre no legible."
    ),
    (
        "Servicio (nombre a completar)",
        "2026-11-12",
        "Mercado",
        "PDF: Miercoles 12. ESTELA 20:30. Tel: 072 212."
    ),
    (
        "Lote 21",
        "2026-11-19",
        "Mercado",
        "PDF: Miercoles 19. Datos a completar."
    ),
    (
        "Premium International",
        "2026-11-22",
        "Mercado",
        "PDF: Sabado 22. Nombre completo no legible."
    ),
    (
        "Especial de Vacunos",
        "2026-11-28",
        "Mercado",
        "PDF: Viernes 28. ESTELA 10. Tel: 072 212."
    ),

    # ── DICIEMBRE 2026 ───────────────────────────────────────────────────────
    (
        "Sale (diciembre 2)",
        "2026-12-02",
        "Mercado",
        "PDF: Miercoles 2. Datos a completar."
    ),
    (
        "Lincoln",
        "2026-12-07",
        None,
        "PDF: 7/12. Datos a completar."
    ),
    (
        "Clunell Ate",
        "2026-12-10",
        None,
        "PDF: 10/12. Datos a completar."
    ),
    (
        "Sale (diciembre 15)",
        "2026-12-15",
        "Mercado",
        "PDF: Martes 15. Datos a completar."
    ),
]


def main():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    insertados = 0
    for titulo, fecha, lugar, notas in REMATES:
        cur.execute(
            '''INSERT INTO remates
               (titulo, fecha_remate, lugar, notas, estado, created_at, updated_at)
               VALUES (?, ?, ?, ?, 'programado', ?, ?)''',
            (titulo, fecha, lugar, notas, now, now)
        )
        insertados += 1
        print(f"  + {titulo} ({fecha[:10]})")

    conn.commit()
    conn.close()
    print(f"\nTotal insertados: {insertados} remates.")


if __name__ == '__main__':
    main()
