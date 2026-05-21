from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from app.core.config import settings

router = APIRouter(tags=["Dashboard"])


@router.get("/", response_class=HTMLResponse)
async def get_dashboard_page():
    html_content = f"""
    <html>
        <head>
            <title>{settings.project_name} Dashboard</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
            <style> body {{ padding: 20px; background-color: #f4f7f6; }} .status-card {{ border-radius: 10px; }} </style>
        </head>
        <body>
            <div class="container">
                <div class="d-flex justify-content-between align-items-center mb-4">
                    <h2 class="text-primary">🛡️ {settings.project_name}</h2>
                    <span class="badge bg-info text-dark">Система активна</span>
                </div>

                <div class="row">
                    <div class="col-md-12 mb-4">
                        <div class="card shadow-sm">
                            <div class="card-header bg-dark text-white">Статус мережевих вузлів</div>
                            <div class="card-body">
                                <table class="table table-hover">
                                    <thead><tr><th>Host</th><th>IP</th><th>Status</th><th>Last Check</th></tr></thead>
                                    <tbody>
                                        <tr><td>Border_Router</td><td>192.168.1.1</td><td><span class="badge bg-success">UP</span></td><td>щойно</td></tr>
                                        <tr><td>Core_Switch</td><td>10.0.0.1</td><td><span class="badge bg-success">UP</span></td><td>5с тому</td></tr>
                                        <tr><td>Access_SW_2</td><td>10.0.2.5</td><td><span class="badge bg-danger">DOWN</span></td><td>10с тому</td></tr>
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="card border-danger shadow-sm">
                    <div class="card-header bg-danger text-white">🚨 Журнал критичних інцидентів</div>
                    <div class="card-body">
                        <ul class="list-group list-group-flush">
                            <li class="list-group-item"><b>14:02:11</b> - Access_SW_2 (10.0.2.5): Втрачено 3 пакети. Вузол недоступний.</li>
                            <li class="list-group-item"><b>11:15:00</b> - Border_Router (192.168.1.1): Навантаження CPU > 90%.</li>
                        </ul>
                    </div>
                </div>
            </div>
        </body>
    </html>
    """
    return html_content