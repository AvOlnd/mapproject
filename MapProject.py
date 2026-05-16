from flask import Flask, jsonify
import json
import os
from datetime import datetime

app = Flask(__name__)
DATA_FILE = 'locations.json'

def load_locations():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            for i, loc in enumerate(data):
                if 'id' not in loc:
                    loc['id'] = i + 1
                if 'category' not in loc:
                    loc['category'] = 'other'
            return data
    return []

def save_locations(locations):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(locations, f, ensure_ascii=False, indent=2)

@app.route('/')
def return_sample_page():
    return '''<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8" />
    <title>Дневник локаций</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
        * { box-sizing: border-box; }
        body { margin: 0; font-family: 'Segoe UI', sans-serif; }
        #map { height: 100vh; width: 100%; }
        .sidebar {
            position: absolute; top: 10px; left: 10px; width: 300px;
            background: white; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.15);
            z-index: 1000; max-height: 90vh; overflow-y: auto;
        }
        .sidebar-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white; padding: 15px; border-radius: 12px 12px 0 0;
            display: flex; justify-content: space-between; align-items: center;
        }
        .sidebar-header h3 { margin: 0; font-size: 18px; }
        .sidebar-toggle {
            background: none; border: none; color: white; font-size: 20px;
            cursor: pointer;
        }
        .sidebar-content { padding: 15px; }
        .sidebar-content.collapsed { display: none; }
        .stats {
            background: #f8f9fa; padding: 10px; border-radius: 8px;
            margin-bottom: 15px; display: flex; justify-content: space-between;
        }
        .stats-item { text-align: center; flex: 1; }
        .stats-number { font-size: 24px; font-weight: bold; color: #667eea; }
        .stats-label { font-size: 12px; color: #666; margin-top: 5px; }
        .filter-group { margin-bottom: 15px; }
        .filter-group label {
            display: block; margin-bottom: 5px; font-weight: bold;
            font-size: 14px; color: #333;
        }
        .category-buttons {
            display: flex; flex-wrap: wrap; gap: 5px; margin-bottom: 10px;
        }
        .category-btn {
            padding: 5px 10px; border: 1px solid #ddd; background: white;
            border-radius: 20px; cursor: pointer; font-size: 12px;
            transition: all 0.2s;
        }
        .category-btn.active {
            background: #667eea; color: white; border-color: #667eea;
        }
        .search-input {
            width: 100%; padding: 8px; border: 1px solid #ddd;
            border-radius: 6px; margin-bottom: 10px;
        }
        .locations-list { max-height: 400px; overflow-y: auto; }
        .location-item {
            background: #f8f9fa; margin-bottom: 8px; padding: 10px;
            border-radius: 8px; cursor: pointer; transition: all 0.2s;
            border-left: 3px solid #667eea;
        }
        .location-item:hover {
            background: #e9ecef; transform: translateX(5px);
        }
        .location-category { font-size: 14px; margin-bottom: 4px; }
        .location-note { font-weight: bold; font-size: 14px; margin-bottom: 4px; }
        .location-details { font-size: 11px; color: #666; }
        .action-buttons {
            display: flex; gap: 10px; margin: 10px 0;
        }
        .btn {
            flex: 1; padding: 8px; border: none; border-radius: 6px;
            cursor: pointer; font-size: 13px; transition: all 0.2s;
        }
        .btn-primary { background: #667eea; color: white; }
        .btn-primary:hover { background: #5a67d8; }
        .btn-danger { background: #f56565; color: white; }
        .btn-danger:hover { background: #e53e3e; }
        .btn-success { background: #48bb78; color: white; }
        .btn-warning { background: #ed8936; color: white; }
        .modal {
            display: none; position: fixed; z-index: 2000; left: 0; top: 0;
            width: 100%; height: 100%; background: rgba(0,0,0,0.5);
        }
        .modal-content {
            background: white; margin: 10% auto; padding: 20px;
            width: 90%; max-width: 500px; border-radius: 12px;
        }
        .modal-header {
            display: flex; justify-content: space-between;
            align-items: center; margin-bottom: 20px;
        }
        .modal-header h3 { margin: 0; }
        .close { font-size: 28px; cursor: pointer; }
        .form-group { margin-bottom: 15px; }
        .form-group label {
            display: block; margin-bottom: 5px; font-weight: bold;
        }
        .form-group input, .form-group select, .form-group textarea {
            width: 100%; padding: 8px; border: 1px solid #ddd;
            border-radius: 6px;
        }
        .toast {
            position: fixed; bottom: 20px; right: 20px;
            background: #333; color: white; padding: 12px 20px;
            border-radius: 8px; z-index: 3000; display: none;
        }
        @media (max-width: 768px) { .sidebar { width: 280px; } }
    </style>
</head>
<body>
    <div class="sidebar">
        <div class="sidebar-header">
            <h3><i class="fas fa-map-marker-alt"></i> Дневник локаций</h3>
            <button class="sidebar-toggle" onclick="toggleSidebar()">
                <i class="fas fa-chevron-left"></i>
            </button>
        </div>
        <div class="sidebar-content" id="sidebarContent">
            <div class="stats">
                <div class="stats-item">
                    <div class="stats-number" id="totalCount">0</div>
                    <div class="stats-label">Всего мест</div>
                </div>
                <div class="stats-item">
                    <div class="stats-number" id="todayCount">0</div>
                    <div class="stats-label">Сегодня</div>
                </div>
            </div>
            
            <div class="filter-group">
                <label><i class="fas fa-filter"></i> Категория</label>
                <div class="category-buttons" id="categoryFilters">
                    <button class="category-btn active" data-category="all">📌 Все</button>
                    <button class="category-btn" data-category="cafe">☕ Кафе</button>
                    <button class="category-btn" data-category="park">🌳 Парк</button>
                    <button class="category-btn" data-category="museum">🏛️ Музей</button>
                    <button class="category-btn" data-category="shop">🛍️ Магазин</button>
                    <button class="category-btn" data-category="other">📌 Другое</button>
                </div>
            </div>
            
            <div class="filter-group">
                <label><i class="fas fa-search"></i> Поиск</label>
                <input type="text" id="searchText" class="search-input" placeholder="Поиск по заметкам...">
            </div>
            
            <div class="action-buttons">
                <button class="btn btn-primary" onclick="getUserLocation()">
                    <i class="fas fa-location-dot"></i> Моё место
                </button>
                <button class="btn btn-success" onclick="exportData()">
                    <i class="fas fa-download"></i> Экспорт
                </button>
            </div>
            
            <div class="action-buttons">
                <button class="btn btn-warning" onclick="importData()">
                    <i class="fas fa-upload"></i> Импорт
                </button>
                <button class="btn btn-danger" onclick="clearAllLocations()">
                    <i class="fas fa-trash"></i> Очистить
                </button>
            </div>
            
            <div class="filter-group">
                <label><i class="fas fa-list"></i> Список (<span id="listCount">0</span>)</label>
                <div class="locations-list" id="locationsList"></div>
            </div>
        </div>
    </div>
    
    <div id="map"></div>
    <div id="toast" class="toast"></div>
    
    <div id="locationModal" class="modal">
        <div class="modal-content">
            <div class="modal-header">
                <h3 id="modalTitle">Добавить место</h3>
                <span class="close" onclick="closeModal()">&times;</span>
            </div>
            <div class="form-group">
                <label>Заметка</label>
                <textarea id="modalNote" rows="3" placeholder="Что здесь?"></textarea>
            </div>
            <div class="form-group">
                <label>Категория</label>
                <select id="modalCategory">
                    <option value="cafe">☕ Кафе/Ресторан</option>
                    <option value="park">🌳 Парк/Природа</option>
                    <option value="museum">🏛️ Музей/Культура</option>
                    <option value="shop">🛍️ Магазин</option>
                    <option value="other">📌 Другое</option>
                </select>
            </div>
            <div class="action-buttons">
                <button class="btn btn-primary" onclick="saveModalLocation()">Сохранить</button>
                <button class="btn" onclick="closeModal()">Отмена</button>
            </div>
        </div>
    </div>

    <script>
    var map = L.map('map').setView([55.751244, 37.618423], 12);
    var markersGroup = L.layerGroup().addTo(map);
    var allLocations = [];
    var currentEditId = null;
    var currentPosition = null;
    var currentFilter = 'all';
    
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap'
    }).addTo(map);
    
    function showToast(msg, isErr = false) {
        var toast = document.getElementById('toast');
        toast.textContent = msg;
        toast.style.background = isErr ? '#f56565' : '#48bb78';
        toast.style.display = 'block';
        setTimeout(() => toast.style.display = 'none', 3000);
    }
    
    function loadMarkers() {
        markersGroup.clearLayers();
        fetch('/api/locations')
            .then(res => res.json())
            .then(locations => {
                allLocations = locations;
                updateStats();
                applyFilters();
            })
            .catch(err => showToast('Ошибка загрузки', true));
    }
    
    function applyFilters() {
        var searchText = document.getElementById('searchText').value.toLowerCase();
        var filtered = allLocations.filter(loc => {
            if (currentFilter !== 'all' && loc.category !== currentFilter) return false;
            if (searchText && !(loc.note || '').toLowerCase().includes(searchText)) return false;
            return true;
        });
        updateMarkers(filtered);
        updateLocationsList(filtered);
        document.getElementById('listCount').innerText = filtered.length;
    }
    
    function getCategoryIcon(cat) {
        var icons = {cafe:'☕', park:'🌳', museum:'🏛️', shop:'🛍️', other:'📌'};
        return icons[cat] || '📌';
    }
    
    function getCategoryName(cat) {
        var names = {cafe:'Кафе', park:'Парк', museum:'Музей', shop:'Магазин', other:'Другое'};
        return names[cat] || 'Другое';
    }
    
    function updateMarkers(locations) {
        markersGroup.clearLayers();
        locations.forEach(loc => {
            var marker = L.marker([loc.lat, loc.lon]).addTo(markersGroup);
            var dist = '';
            if (currentPosition) {
                var d = calculateDistance(currentPosition.lat, currentPosition.lon, loc.lat, loc.lon);
                dist = `<div style="color:#4caf50">📏 ${d} км от вас</div>`;
            }
            var popup = `
                <div>
                    <div>${getCategoryIcon(loc.category)} ${getCategoryName(loc.category)}</div>
                    <div><strong>📝 ${loc.note || 'Без названия'}</strong></div>
                    <div>📅 ${loc.timestamp || ''}</div>
                    ${dist}
                    <div style="margin-top:10px">
                        <button onclick="editLocationById(${loc.id})" style="background:#2196F3;color:white;padding:5px 10px;margin-right:5px;border:none;border-radius:4px">
                            ✏️ Ред.
                        </button>
                        <button onclick="deleteLocation(${loc.id})" style="background:#f44336;color:white;padding:5px 10px;border:none;border-radius:4px">
                            🗑️ Удал.
                        </button>
                    </div>
                </div>
            `;
            marker.bindPopup(popup);
        });
    }
    
    function calculateDistance(lat1, lon1, lat2, lon2) {
        var R = 6371;
        var dLat = (lat2 - lat1) * Math.PI / 180;
        var dLon = (lon2 - lon1) * Math.PI / 180;
        var a = Math.sin(dLat/2) * Math.sin(dLat/2) +
                Math.cos(lat1 * Math.PI/180) * Math.cos(lat2 * Math.PI/180) *
                Math.sin(dLon/2) * Math.sin(dLon/2);
        var c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
        return Math.round(R * c * 10) / 10;
    }
    
    function updateLocationsList(locations) {
        var html = '';
        locations.forEach(loc => {
            var dist = '';
            if (currentPosition) {
                var d = calculateDistance(currentPosition.lat, currentPosition.lon, loc.lat, loc.lon);
                dist = `<div style="color:#4caf50">📏 ${d} км</div>`;
            }
            html += `
                <div class="location-item" onclick="zoomTo(${loc.lat}, ${loc.lon})">
                    <div class="location-category">${getCategoryIcon(loc.category)} ${getCategoryName(loc.category)}</div>
                    <div class="location-note">${loc.note || 'Без названия'}</div>
                    <div class="location-details">${loc.timestamp || ''}</div>
                    ${dist}
                </div>
            `;
        });
        if (!html) html = '<div style="text-align:center;padding:20px;color:#999">Нет локаций</div>';
        document.getElementById('locationsList').innerHTML = html;
    }
    
    function zoomTo(lat, lon) {
        map.setView([lat, lon], 15);
    }
    
    function updateStats() {
        document.getElementById('totalCount').innerText = allLocations.length;
        var today = new Date().toLocaleDateString();
        var cnt = allLocations.filter(l => l.timestamp && l.timestamp.includes(today)).length;
        document.getElementById('todayCount').innerText = cnt;
    }
    
    window.saveLocation = function(lat, lng, note, category) {
        fetch('/api/locations', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                lat: lat, lon: lng, note: note,
                timestamp: new Date().toLocaleString(),
                category: category
            })
        })
        .then(res => res.json())
        .then(() => { loadMarkers(); showToast('Сохранено!'); })
        .catch(() => showToast('Ошибка', true));
    };
    
    window.editLocationById = function(id) {
        var loc = allLocations.find(l => l.id === id);
        if (loc) {
            currentEditId = id;
            document.getElementById('modalTitle').innerText = 'Редактировать';
            document.getElementById('modalNote').value = loc.note || '';
            document.getElementById('modalCategory').value = loc.category || 'other';
            document.getElementById('locationModal').style.display = 'block';
        }
    };
    
    window.deleteLocation = function(id) {
        if (confirm('Удалить?')) {
            fetch(`/api/locations/${id}`, {method: 'DELETE'})
                .then(() => { loadMarkers(); showToast('Удалено'); });
        }
    };
    
    window.clearAllLocations = function() {
        if (confirm('Удалить всё?')) {
            fetch('/api/locations', {method: 'DELETE'})
                .then(() => { loadMarkers(); showToast('Все удалены'); });
        }
    };
    
    window.exportData = function() {
        var data = JSON.stringify(allLocations, null, 2);
        var link = document.createElement('a');
        link.download = 'locations.json';
        link.href = 'data:application/json,' + encodeURIComponent(data);
        link.click();
        showToast('Экспорт готов');
    };
    
    window.importData = function() {
        var input = document.createElement('input');
        input.type = 'file';
        input.accept = 'application/json';
        input.onchange = e => {
            var file = e.target.files[0];
            var reader = new FileReader();
            reader.onload = evt => {
                try {
                    var locations = JSON.parse(evt.target.result);
                    locations.forEach(loc => {
                        fetch('/api/locations', {
                            method: 'POST',
                            headers: {'Content-Type': 'application/json'},
                            body: JSON.stringify(loc)
                        });
                    });
                    setTimeout(() => { loadMarkers(); showToast('Импорт завершен'); }, 500);
                } catch(err) { showToast('Ошибка импорта', true); }
            };
            reader.readAsText(file);
        };
        input.click();
    };
    
    window.getUserLocation = function() {
        if ('geolocation' in navigator) {
            navigator.geolocation.getCurrentPosition(pos => {
                currentPosition = {lat: pos.coords.latitude, lon: pos.coords.longitude};
                map.setView([currentPosition.lat, currentPosition.lon], 13);
                L.marker([currentPosition.lat, currentPosition.lon])
                    .bindPopup('📍 Вы здесь')
                    .addTo(map);
                applyFilters();
                showToast('Местоположение определено');
            });
        } else { showToast('Геолокация не поддерживается', true); }
    };
    
    map.on('click', e => {
        currentEditId = null;
        document.getElementById('modalTitle').innerText = 'Добавить место';
        document.getElementById('modalNote').value = '';
        document.getElementById('modalCategory').value = 'other';
        document.getElementById('locationModal').style.display = 'block';
        window.pendingLocation = {lat: e.latlng.lat, lng: e.latlng.lng};
    });
    
    function closeModal() {
        document.getElementById('locationModal').style.display = 'none';
        window.pendingLocation = null;
        currentEditId = null;
    }
    
    function saveModalLocation() {
        var note = document.getElementById('modalNote').value;
        var category = document.getElementById('modalCategory').value;
        
        if (currentEditId) {
            fetch(`/api/locations/${currentEditId}`, {
                method: 'PUT',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({note: note, category: category})
            })
            .then(() => { loadMarkers(); closeModal(); showToast('Обновлено!'); });
        } else if (window.pendingLocation) {
            saveLocation(window.pendingLocation.lat, window.pendingLocation.lng, note, category);
            closeModal();
        }
    }
    
    document.getElementById('searchText').addEventListener('input', applyFilters);
    document.querySelectorAll('.category-btn').forEach(btn => {
        btn.onclick = function() {
            document.querySelectorAll('.category-btn').forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            currentFilter = this.dataset.category;
            applyFilters();
        };
    });
    
    function toggleSidebar() {
        var content = document.getElementById('sidebarContent');
        var btn = document.querySelector('.sidebar-toggle i');
        content.classList.toggle('collapsed');
        btn.classList.toggle('fa-chevron-left');
        btn.classList.toggle('fa-chevron-right');
    }
    
    loadMarkers();
    </script>
</body>
</html>'''

# API endpoints
@app.route('/api/locations', methods=['GET'])
def get_locations():
    return jsonify(load_locations())

@app.route('/api/locations', methods=['POST'])
def add_location():
    data = request.get_json()
    locations = load_locations()
    new_id = max([l.get('id', 0) for l in locations]) + 1 if locations else 1
    new_loc = {
        'id': new_id, 'lat': data['lat'], 'lon': data['lon'],
        'note': data.get('note', ''), 'timestamp': data.get('timestamp', datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
        'category': data.get('category', 'other')
    }
    locations.append(new_loc)
    save_locations(locations)
    return jsonify({'status': 'success'})

@app.route('/api/locations/<int:location_id>', methods=['PUT'])
def update_location(location_id):
    data = request.get_json()
    locations = load_locations()
    for loc in locations:
        if loc.get('id') == location_id:
            if 'note' in data: loc['note'] = data['note']
            if 'category' in data: loc['category'] = data['category']
            save_locations(locations)
            return jsonify({'status': 'success'})
    return jsonify({'status': 'error'}), 404

@app.route('/api/locations/<int:location_id>', methods=['DELETE'])
def delete_location(location_id):
    locations = load_locations()
    locations = [l for l in locations if l.get('id') != location_id]
    save_locations(locations)
    return jsonify({'status': 'success'})

@app.route('/api/locations', methods=['DELETE'])
def delete_all_locations():
    save_locations([])
    return jsonify({'status': 'success'})

if __name__ == '__main__':
    from flask import request
    app.run(debug=True)
