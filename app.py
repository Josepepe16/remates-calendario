from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import sqlite3
import os
from datetime import datetime, timedelta, date

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.environ.get('REMATES_DATA_DIR', BASE_DIR)
DB_PATH = os.path.join(DATA_DIR, 'remates.db')

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, 'templates'),
    static_folder=os.path.join(BASE_DIR, 'static'),
)
app.secret_key = os.environ.get('SECRET_KEY', 'remates-calendario-2026-secretkey')

ESTADOS = ['programado', 'en_progreso', 'finalizado', 'cancelado']
PLATAFORMAS = ['YouTube', 'Facebook', 'Instagram', 'TikTok', 'Zoom', 'Otro']
STATUS_COLORS = {
    'programado': '#0d6efd',
    'en_progreso': '#fd7e14',
    'finalizado': '#198754',
    'cancelado': '#adb5bd',
}
STATUS_LABELS = {
    'programado': 'Programado',
    'en_progreso': 'En progreso',
    'finalizado': 'Finalizado',
    'cancelado': 'Cancelado',
}


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    os.makedirs(DATA_DIR, exist_ok=True)
    with get_db() as db:
        db.executescript('''
            CREATE TABLE IF NOT EXISTS remates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                titulo TEXT NOT NULL,
                fecha_remate TEXT NOT NULL,
                lugar TEXT,
                establecimiento TEXT,
                ciudad TEXT,
                provincia TEXT,
                transmision_nombre TEXT,
                transmision_plataforma TEXT,
                transmision_url TEXT,
                retransmision_nombre TEXT,
                retransmision_plataforma TEXT,
                retransmision_url TEXT,
                catalogo_descripcion TEXT,
                catalogo_url TEXT,
                cantidad_lotes INTEGER,
                fecha_fotos TEXT,
                responsable_fotos TEXT,
                fecha_videos TEXT,
                responsable_videos TEXT,
                catalogo_listo INTEGER DEFAULT 0,
                fotos_listas INTEGER DEFAULT 0,
                videos_listos INTEGER DEFAULT 0,
                transmision_configurada INTEGER DEFAULT 0,
                estado TEXT DEFAULT 'programado',
                notas TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
        ''')


def remate_to_dict(r):
    return {
        'id': r['id'],
        'titulo': r['titulo'],
        'fecha_remate': r['fecha_remate'],
        'lugar': r['lugar'],
        'establecimiento': r['establecimiento'],
        'ciudad': r['ciudad'],
        'provincia': r['provincia'],
        'transmision_nombre': r['transmision_nombre'],
        'transmision_plataforma': r['transmision_plataforma'],
        'transmision_url': r['transmision_url'],
        'retransmision_nombre': r['retransmision_nombre'],
        'retransmision_plataforma': r['retransmision_plataforma'],
        'retransmision_url': r['retransmision_url'],
        'catalogo_descripcion': r['catalogo_descripcion'],
        'catalogo_url': r['catalogo_url'],
        'cantidad_lotes': r['cantidad_lotes'],
        'fecha_fotos': r['fecha_fotos'],
        'responsable_fotos': r['responsable_fotos'],
        'fecha_videos': r['fecha_videos'],
        'responsable_videos': r['responsable_videos'],
        'catalogo_listo': bool(r['catalogo_listo']),
        'fotos_listas': bool(r['fotos_listas']),
        'videos_listos': bool(r['videos_listos']),
        'transmision_configurada': bool(r['transmision_configurada']),
        'estado': r['estado'],
        'notas': r['notas'],
        'created_at': r['created_at'],
        'updated_at': r['updated_at'],
    }


def get_autocomplete_names():
    with get_db() as db:
        rows = db.execute(
            'SELECT transmision_nombre, retransmision_nombre, '
            'responsable_fotos, responsable_videos FROM remates'
        ).fetchall()
    names = set()
    for row in rows:
        for val in [row['transmision_nombre'], row['retransmision_nombre'],
                    row['responsable_fotos'], row['responsable_videos']]:
            if val:
                names.add(val.strip())
    return sorted(names)


def get_autocomplete_lugares():
    with get_db() as db:
        rows = db.execute(
            'SELECT DISTINCT lugar FROM remates WHERE lugar IS NOT NULL AND lugar != ""'
        ).fetchall()
    return [r['lugar'] for r in rows]


# ─── Routes ──────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    now = datetime.now()
    hoy = now.date()
    en_30_dias = hoy + timedelta(days=30)
    with get_db() as db:
        proximos = db.execute(
            "SELECT * FROM remates WHERE estado IN ('programado','en_progreso') "
            "AND DATE(fecha_remate) >= ? ORDER BY fecha_remate ASC LIMIT 10",
            (hoy.isoformat(),)
        ).fetchall()
        pendientes_fotos = db.execute(
            "SELECT * FROM remates WHERE fotos_listas=0 AND fecha_fotos IS NOT NULL "
            "AND fecha_fotos != '' AND DATE(fecha_fotos) >= ? AND estado != 'cancelado' "
            "ORDER BY fecha_fotos ASC LIMIT 5",
            (hoy.isoformat(),)
        ).fetchall()
        pendientes_videos = db.execute(
            "SELECT * FROM remates WHERE videos_listos=0 AND fecha_videos IS NOT NULL "
            "AND fecha_videos != '' AND DATE(fecha_videos) >= ? AND estado != 'cancelado' "
            "ORDER BY fecha_videos ASC LIMIT 5",
            (hoy.isoformat(),)
        ).fetchall()
        stats = {}
        for estado in ESTADOS:
            row = db.execute(
                'SELECT COUNT(*) as cnt FROM remates WHERE estado=?', (estado,)
            ).fetchone()
            stats[estado] = row['cnt']
        stats['total'] = sum(stats.values())
    return render_template(
        'index.html',
        proximos=proximos,
        pendientes_fotos=pendientes_fotos,
        pendientes_videos=pendientes_videos,
        stats=stats,
        active_page='inicio',
        STATUS_LABELS=STATUS_LABELS,
        ahora=now,
    )


@app.route('/calendario')
def calendario():
    return render_template('calendario.html', active_page='calendario')


@app.route('/api/eventos')
def api_eventos():
    with get_db() as db:
        rows = db.execute('SELECT * FROM remates ORDER BY fecha_remate').fetchall()
    eventos = []
    for r in rows:
        fecha = r['fecha_remate']
        color = STATUS_COLORS.get(r['estado'], '#6c757d')
        eventos.append({
            'id': r['id'],
            'title': r['titulo'],
            'start': fecha,
            'color': color,
            'url': f'/remate/{r["id"]}',
            'extendedProps': {
                'estado': STATUS_LABELS.get(r['estado'], r['estado']),
                'lugar': r['lugar'] or '',
                'ciudad': r['ciudad'] or '',
            }
        })
        if r['fecha_fotos']:
            eventos.append({
                'id': f'fotos-{r["id"]}',
                'title': f'📷 Fotos: {r["titulo"]}',
                'start': r['fecha_fotos'],
                'color': '#6f42c1',
                'url': f'/remate/{r["id"]}',
                'display': 'list-item',
            })
        if r['fecha_videos']:
            eventos.append({
                'id': f'videos-{r["id"]}',
                'title': f'🎥 Videos: {r["titulo"]}',
                'start': r['fecha_videos'],
                'color': '#e83e8c',
                'url': f'/remate/{r["id"]}',
                'display': 'list-item',
            })
    return jsonify(eventos)


@app.route('/remates')
def remates():
    estado_filtro = request.args.get('estado', 'todos')
    q = request.args.get('q', '').strip()
    with get_db() as db:
        sql = 'SELECT * FROM remates WHERE 1=1'
        params = []
        if estado_filtro != 'todos':
            sql += ' AND estado=?'
            params.append(estado_filtro)
        if q:
            sql += ' AND (titulo LIKE ? OR lugar LIKE ? OR ciudad LIKE ?)'
            params += [f'%{q}%', f'%{q}%', f'%{q}%']
        sql += ' ORDER BY fecha_remate DESC'
        rows = db.execute(sql, params).fetchall()
        counts = {'todos': 0}
        for estado in ESTADOS:
            c = db.execute('SELECT COUNT(*) as cnt FROM remates WHERE estado=?', (estado,)).fetchone()
            counts[estado] = c['cnt']
            counts['todos'] += c['cnt']
    return render_template(
        'remates.html',
        remates=rows,
        estado_filtro=estado_filtro,
        counts=counts,
        q=q,
        active_page='remates',
        STATUS_LABELS=STATUS_LABELS,
    )


@app.route('/remate/nuevo', methods=['GET', 'POST'])
def nuevo_remate():
    if request.method == 'POST':
        return _guardar_remate(None)
    nombres = get_autocomplete_names()
    lugares = get_autocomplete_lugares()
    return render_template(
        'remate_form.html',
        remate=None,
        accion='Nuevo Remate',
        active_page='remates',
        PLATAFORMAS=PLATAFORMAS,
        ESTADOS=ESTADOS,
        STATUS_LABELS=STATUS_LABELS,
        nombres=nombres,
        lugares=lugares,
    )


@app.route('/remate/<int:rid>')
def ver_remate(rid):
    with get_db() as db:
        r = db.execute('SELECT * FROM remates WHERE id=?', (rid,)).fetchone()
    if not r:
        flash('Remate no encontrado', 'danger')
        return redirect(url_for('remates'))
    return render_template(
        'remate_detail.html',
        r=r,
        active_page='remates',
        STATUS_LABELS=STATUS_LABELS,
        STATUS_COLORS=STATUS_COLORS,
        ESTADOS=ESTADOS,
    )


@app.route('/remate/<int:rid>/editar', methods=['GET', 'POST'])
def editar_remate(rid):
    with get_db() as db:
        r = db.execute('SELECT * FROM remates WHERE id=?', (rid,)).fetchone()
    if not r:
        flash('Remate no encontrado', 'danger')
        return redirect(url_for('remates'))
    if request.method == 'POST':
        return _guardar_remate(rid)
    nombres = get_autocomplete_names()
    lugares = get_autocomplete_lugares()
    return render_template(
        'remate_form.html',
        remate=r,
        accion='Editar Remate',
        active_page='remates',
        PLATAFORMAS=PLATAFORMAS,
        ESTADOS=ESTADOS,
        STATUS_LABELS=STATUS_LABELS,
        nombres=nombres,
        lugares=lugares,
    )


def _guardar_remate(rid):
    f = request.form
    titulo = f.get('titulo', '').strip()
    fecha_remate = f.get('fecha_remate', '').strip()
    if not titulo:
        flash('El título es obligatorio.', 'danger')
        return redirect(request.referrer or url_for('nuevo_remate'))
    if not fecha_remate:
        flash('La fecha del remate es obligatoria.', 'danger')
        return redirect(request.referrer or url_for('nuevo_remate'))

    # Combine date + time
    hora = f.get('hora_remate', '').strip()
    if hora:
        fecha_remate = f'{fecha_remate}T{hora}'

    cantidad_lotes = f.get('cantidad_lotes', '').strip()
    cantidad_lotes = int(cantidad_lotes) if cantidad_lotes.isdigit() else None

    params = (
        titulo,
        fecha_remate,
        f.get('lugar', '').strip() or None,
        f.get('establecimiento', '').strip() or None,
        f.get('ciudad', '').strip() or None,
        f.get('provincia', '').strip() or None,
        f.get('transmision_nombre', '').strip() or None,
        f.get('transmision_plataforma', '').strip() or None,
        f.get('transmision_url', '').strip() or None,
        f.get('retransmision_nombre', '').strip() or None,
        f.get('retransmision_plataforma', '').strip() or None,
        f.get('retransmision_url', '').strip() or None,
        f.get('catalogo_descripcion', '').strip() or None,
        f.get('catalogo_url', '').strip() or None,
        cantidad_lotes,
        f.get('fecha_fotos', '').strip() or None,
        f.get('responsable_fotos', '').strip() or None,
        f.get('fecha_videos', '').strip() or None,
        f.get('responsable_videos', '').strip() or None,
        f.get('estado', 'programado'),
        f.get('notas', '').strip() or None,
        datetime.now().isoformat(),
    )

    with get_db() as db:
        if rid is None:
            db.execute(
                '''INSERT INTO remates (
                    titulo, fecha_remate, lugar, establecimiento, ciudad, provincia,
                    transmision_nombre, transmision_plataforma, transmision_url,
                    retransmision_nombre, retransmision_plataforma, retransmision_url,
                    catalogo_descripcion, catalogo_url, cantidad_lotes,
                    fecha_fotos, responsable_fotos, fecha_videos, responsable_videos,
                    estado, notas, updated_at
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
                params
            )
            new_id = db.execute('SELECT last_insert_rowid()').fetchone()[0]
            flash('Remate creado correctamente.', 'success')
            return redirect(url_for('ver_remate', rid=new_id))
        else:
            db.execute(
                '''UPDATE remates SET
                    titulo=?, fecha_remate=?, lugar=?, establecimiento=?, ciudad=?, provincia=?,
                    transmision_nombre=?, transmision_plataforma=?, transmision_url=?,
                    retransmision_nombre=?, retransmision_plataforma=?, retransmision_url=?,
                    catalogo_descripcion=?, catalogo_url=?, cantidad_lotes=?,
                    fecha_fotos=?, responsable_fotos=?, fecha_videos=?, responsable_videos=?,
                    estado=?, notas=?, updated_at=?
                WHERE id=?''',
                params + (rid,)
            )
            flash('Remate actualizado correctamente.', 'success')
            return redirect(url_for('ver_remate', rid=rid))


@app.route('/remate/<int:rid>/estado', methods=['POST'])
def cambiar_estado(rid):
    nuevo = request.form.get('estado')
    if nuevo not in ESTADOS:
        flash('Estado inválido.', 'danger')
        return redirect(url_for('ver_remate', rid=rid))
    with get_db() as db:
        db.execute(
            'UPDATE remates SET estado=?, updated_at=? WHERE id=?',
            (nuevo, datetime.now().isoformat(), rid)
        )
    flash(f'Estado cambiado a {STATUS_LABELS[nuevo]}.', 'success')
    return redirect(url_for('ver_remate', rid=rid))


@app.route('/remate/<int:rid>/checklist', methods=['POST'])
def actualizar_checklist(rid):
    campo = request.form.get('campo')
    valor = 1 if request.form.get('valor') == '1' else 0
    campos_validos = ['catalogo_listo', 'fotos_listas', 'videos_listos', 'transmision_configurada']
    if campo not in campos_validos:
        return jsonify({'ok': False}), 400
    with get_db() as db:
        db.execute(
            f'UPDATE remates SET {campo}=?, updated_at=? WHERE id=?',
            (valor, datetime.now().isoformat(), rid)
        )
    return jsonify({'ok': True, 'valor': valor})


@app.route('/remate/<int:rid>/eliminar', methods=['POST'])
def eliminar_remate(rid):
    with get_db() as db:
        r = db.execute('SELECT titulo FROM remates WHERE id=?', (rid,)).fetchone()
        if not r:
            flash('Remate no encontrado.', 'danger')
            return redirect(url_for('remates'))
        db.execute('DELETE FROM remates WHERE id=?', (rid,))
    flash(f'Remate "{r["titulo"]}" eliminado.', 'success')
    return redirect(url_for('remates'))


# ─── Jinja helpers ───────────────────────────────────────────────────────────

@app.template_filter('fecha_legible')
def fecha_legible(value):
    if not value:
        return ''
    try:
        dt = datetime.fromisoformat(value.replace('Z', ''))
        meses = ['ene', 'feb', 'mar', 'abr', 'may', 'jun',
                 'jul', 'ago', 'sep', 'oct', 'nov', 'dic']
        return f'{dt.day} {meses[dt.month - 1]} {dt.year}, {dt.strftime("%H:%M")}' if dt.hour else f'{dt.day} {meses[dt.month - 1]} {dt.year}'
    except Exception:
        return value


@app.template_filter('fecha_corta')
def fecha_corta(value):
    if not value:
        return ''
    try:
        dt = datetime.fromisoformat(value.replace('Z', ''))
        meses = ['ene', 'feb', 'mar', 'abr', 'may', 'jun',
                 'jul', 'ago', 'sep', 'oct', 'nov', 'dic']
        return f'{dt.day} {meses[dt.month - 1]}'
    except Exception:
        return value


@app.template_filter('dias_restantes')
def dias_restantes(value):
    if not value:
        return ''
    try:
        dt = datetime.fromisoformat(value.replace('Z', '')).date()
        diff = (dt - date.today()).days
        if diff < 0:
            return f'hace {-diff}d'
        if diff == 0:
            return 'HOY'
        if diff == 1:
            return 'mañana'
        return f'en {diff}d'
    except Exception:
        return ''


if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5001)

init_db()
